# Future work

The current product supports local end-to-end changed-code coverage review.
Track delivery status in the [checklist](03_TASK_CHECKLIST.md); this page records
possible follow-ups, not existing capabilities or delivery commitments.

## Near-term validation

- Validate a small representative set of real committed C# diffs, with manual
  findings and unknown/discrepancy causes recorded.
- Run the voluntary reviewer-time pilot if reviewer usefulness needs to be measured.
- Consider report-only CI that runs tests, collects coverage, invokes TC1 and
  publishes artifacts after sampled mapping validation. No provider is selected.

## CI gate: deferred

There is no trustworthy default threshold today. A percentage alone can hide too
little classifiable evidence, many unknowns or broad exclusions. Before implementing
any blocking gate, the team must validate representative mappings and explicitly
choose a policy covering:

- line and branch criteria and their separate denominators;
- unknown evidence and minimum classifiable evidence;
- explicit exclusions and empty-diff / null-coverage cases;
- collection failures or coverage from the wrong revision;
- threshold justification from observed project data and an approved rollout.

These are unresolved design decisions. No numeric threshold or fail-on-coverage
behavior is introduced by the current CLI.

## Separate extensions

PR annotations, project exclusion configuration, coverage provenance checks and
additional validated collectors may be useful after the pilot. Broader changes
such as multi-language support, mutation testing, dependency graphs, risk scoring,
AI summaries or a hosted dashboard require separately agreed scope. Coverage facts
must continue to come from instrumentation.
