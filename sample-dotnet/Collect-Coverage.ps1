[CmdletBinding()]
param(
    [string]$Dotnet = 'dotnet'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Resolve the executable before changing directories; no implicit SDK fallback.
$dotnetPath = (Get-Command $Dotnet -CommandType Application -ErrorAction Stop).Source
$gitPath = (Get-Command git -CommandType Application -ErrorAction Stop).Source
$repoRoot = Split-Path $PSScriptRoot -Parent
$runId = 'wp1-' + [Guid]::NewGuid().ToString('N')
$runDirectory = Join-Path $repoRoot "artifacts/test-results/$runId"
$bundleDirectory = Join-Path $repoRoot 'artifacts/tc1'
$runHtml = Join-Path $runDirectory 'coverage'
$environment = @{
    DOTNET_ROOT = Split-Path $dotnetPath -Parent
    DOTNET_CLI_HOME = Join-Path $repoRoot 'artifacts/tools/dotnet-home'
    NUGET_PACKAGES = Join-Path $repoRoot 'artifacts/tools/nuget-packages'
    DOTNET_CLI_TELEMETRY_OPTOUT = '1'
    DOTNET_GENERATE_ASPNET_CERTIFICATE = 'false'
    DOTNET_SKIP_FIRST_TIME_EXPERIENCE = '1'
}
$previousEnvironment = @{}
$transcribing = $false
$collectionCommit = (& $gitPath -C $repoRoot rev-parse --verify 'HEAD^{commit}').Trim()
if ($LASTEXITCODE -ne 0 -or $collectionCommit -notmatch '^[0-9a-f]{40,64}$') {
    throw 'Cannot resolve the committed head used for coverage collection.'
}
$dirtyEntries = @(& $gitPath -C $repoRoot status --porcelain=v1 --untracked-files=all)
if ($LASTEXITCODE -ne 0) { throw 'Cannot determine worktree state before coverage collection.' }
$collectionDirty = $dirtyEntries.Count -gt 0

function Invoke-SampleDotnet {
    param([string[]]$Arguments)
    & $dotnetPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "dotnet $($Arguments[0]) failed (exit $LASTEXITCODE). See $runDirectory."
    }
}

Push-Location $PSScriptRoot
try {
    foreach ($key in $environment.Keys) {
        $previousEnvironment[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
        [Environment]::SetEnvironmentVariable($key, $environment[$key], 'Process')
    }
    New-Item -ItemType Directory -Path $runDirectory -Force | Out-Null
    Start-Transcript -Path (Join-Path $runDirectory 'collection.log') | Out-Null
    $transcribing = $true
    $sdkVersion = & $dotnetPath --version
    if ($LASTEXITCODE -ne 0) { throw 'The selected dotnet executable has no compatible SDK.' }

    Invoke-SampleDotnet -Arguments @('restore', 'Tc1.Sample.slnx', '--configfile', 'NuGet.Config')
    Invoke-SampleDotnet -Arguments @('tool', 'restore', '--tool-manifest', '.config/dotnet-tools.json', '--configfile', 'NuGet.Config')
    Invoke-SampleDotnet -Arguments @('build', 'Tc1.Sample.slnx', '--no-restore', '--configuration', 'Debug')
    Invoke-SampleDotnet -Arguments @('test', 'Tc1.Sample.slnx', '--no-build', '--configuration', 'Debug',
        '--settings', 'coverage.runsettings', '--collect', 'XPlat Code Coverage',
        '--results-directory', $runDirectory, '--logger', 'trx;LogFileName=sample-tests.trx')

    [xml]$testResult = Get-Content -LiteralPath (Join-Path $runDirectory 'sample-tests.trx') -Raw
    $summary = $testResult.TestRun.ResultSummary
    if ($summary.outcome -ne 'Completed' -or [int]$summary.Counters.executed -le 0 -or
        [int]$summary.Counters.failed -ne 0 -or
        [int]$summary.Counters.passed -ne [int]$summary.Counters.total) {
        throw 'The run did not pass all discovered sample tests; no baseline will be published.'
    }

    # VSTest also copies collector output into the TRX deployment folder.
    # Resolve the attachment declared by this run instead of scanning duplicate files.
    $namespaces = [System.Xml.XmlNamespaceManager]::new($testResult.NameTable)
    $namespaces.AddNamespace('trx', $testResult.DocumentElement.NamespaceURI)
    $attachments = @($testResult.SelectNodes(
        '/trx:TestRun/trx:ResultSummary/trx:CollectorDataEntries/trx:Collector[@uri="datacollector://microsoft/CoverletCodeCoverage/1.0"]/trx:UriAttachments/trx:UriAttachment/trx:A',
        $namespaces))
    if ($attachments.Count -ne 1) {
        throw "Expected one Coverlet attachment in TRX; found $($attachments.Count)."
    }
    $attachment = $attachments[0].GetAttribute('href').Replace('\', [IO.Path]::DirectorySeparatorChar)
    if ([IO.Path]::GetFileName($attachment) -ne 'coverage.cobertura.xml') {
        throw 'The Coverlet attachment is not a Cobertura export.'
    }
    $deployment = $testResult.TestRun.TestSettings.Deployment.runDeploymentRoot
    $coveragePath = [IO.Path]::GetFullPath((Join-Path (Join-Path (Join-Path $runDirectory $deployment) 'In') $attachment))
    $runPrefix = [IO.Path]::GetFullPath($runDirectory) + [IO.Path]::DirectorySeparatorChar
    if (-not $coveragePath.StartsWith($runPrefix, [StringComparison]::OrdinalIgnoreCase) -or
        -not (Test-Path -LiteralPath $coveragePath -PathType Leaf)) {
        throw 'The TRX coverage attachment is missing or outside the current run.'
    }
    [xml]$coverage = Get-Content -LiteralPath $coveragePath -Raw
    if ($coverage.DocumentElement.Name -ne 'coverage' -or
        $coverage.SelectNodes('/coverage/packages/package/classes/class/lines/line').Count -eq 0) {
        throw 'The collector produced no usable Cobertura line evidence.'
    }

    Invoke-SampleDotnet -Arguments @('tool', 'run', 'reportgenerator', '--',
        "-reports:$($coveragePath)", "-targetdir:$runHtml",
        '-reporttypes:Html;TextSummary', '-riskhotspotassemblyfilters:-*',
        '-title:TC1 sample coverage baseline')
    if (-not (Test-Path -LiteralPath (Join-Path $runHtml 'index.html'))) {
        throw 'ReportGenerator did not produce index.html.'
    }

    # Cobertura is already the normalized format: preserve the export byte-for-byte.
    New-Item -ItemType Directory -Path (Join-Path $bundleDirectory 'coverage') -Force | Out-Null
    Copy-Item -LiteralPath $coveragePath -Destination (Join-Path $bundleDirectory 'coverage.cobertura.xml') -Force
    Copy-Item -Path (Join-Path $runHtml '*') -Destination (Join-Path $bundleDirectory 'coverage') -Recurse -Force
    $metadata = [ordered]@{
        schema_version = '1.0'
        commit_sha = $collectionCommit
        dirty_state = $collectionDirty
        collector = 'coverlet.collector'
        collector_version = '6.0.4'
        collection_command = 'dotnet test Tc1.Sample.slnx --no-build --configuration Debug --settings coverage.runsettings --collect XPlat Code Coverage'
        target_framework = 'net10.0'
        coverage_xml_sha256 = (Get-FileHash $coveragePath -Algorithm SHA256).Hash.ToLowerInvariant()
        timestamp = [DateTime]::UtcNow.ToString('O')
        run_id = $runId
        sdk_version = $sdkVersion
        configuration = 'Debug'
        source_sha256 = (Get-FileHash (Join-Path $PSScriptRoot 'Tc1.Sample/DiscountService.cs') -Algorithm SHA256).Hash
        raw_results = "artifacts/test-results/$runId"
        report_generator = '5.5.11'
    }
    $metadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runDirectory 'run.json') -Encoding UTF8
    Copy-Item -LiteralPath (Join-Path $runDirectory 'run.json') -Destination (Join-Path $bundleDirectory 'coverage-run.json') -Force
    Write-Output "Coverage bundle: $bundleDirectory"
    Write-Output "Raw evidence: $runDirectory"
} finally {
    if ($transcribing) { Stop-Transcript | Out-Null }
    foreach ($key in $previousEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($key, $previousEnvironment[$key], 'Process')
    }
    Pop-Location
}
