# Start Here

## 1. Purpose of this repo

This is a **standalone TC1 side project**.

Do not assume access to any company/DMS workspace.

The immediate goal is to build and validate the TC1 MVP locally.

## 2. What TC1 does

```text
Git diff
= what changed?

Coverage
= what did tests execute?

TC1
= which changed code was or was not exercised?
```

## 3. Local-first strategy

Because the real target repository may be unavailable at the beginning:

### Stage A — controlled local pilot

Use a small C# sample inside:

```text
sample-dotnet/
```

Purpose:
- develop the mapper;
- validate semantics;
- create deterministic fixtures;
- prove the CLI/report flow.

### Stage B — real pilot later

When access to a real C# repository is available:

- keep TC1 architecture unchanged;
- point TC1 at the real repo;
- select compatible coverage tooling;
- validate mappings on sampled real diffs.

Do not hard-code the local sample into the TC1 engine.

## 4. Recommended working order

```text
WP0  environment + local pilot
WP1  coverage baseline
WP2  Python bootstrap
WP3  Git diff parser
WP4  Cobertura parser
WP5  path normalization
WP6  line mapper
WP7  branch mapper
WP8  metrics
WP9  reports
WP10 evaluation
WP11 [real-pilot readiness](23_REAL_PILOT_READINESS.md) (execution when access is available)
WP12 optional report-only CI
WP13 optional CI gate (post-MVP, explicit approval required)
```

Work package numbers follow [Implementation Plan](05_IMPLEMENTATION_PLAN.md).
Handover documentation is maintained throughout the work and finalized for the local MVP;
it does not depend on optional CI or access to a real pilot.

## 5. What not to do yet

Do not start with:
- LLMs;
- Graft;
- OpenCodeReview integration;
- dashboards;
- Docker/Kubernetes;
- DB;
- multi-language support.

The first success criterion is a correct deterministic mapper.
