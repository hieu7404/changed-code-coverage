# Reference Notes

These are references, not runtime dependencies.

## Microsoft/.NET coverage guidance

Use official .NET coverage guidance when configuring the pilot collector.

## Coverlet

Preferred initial .NET coverage collector when compatible.

Role:
- instrument/run tests;
- produce coverage evidence.

## Cobertura XML

Initial normalized interchange format consumed by TC1.

## ReportGenerator

Role:
- turn coverage export into readable HTML;
- provide supporting evidence.

It does not calculate TC1 changed-code mapping.

## Alibaba OpenCodeReview

Potential ideas:
- Git diff handling;
- line-level review annotations;
- CI/review publishing.

Do not integrate it into MVP by default.

## Graft

Potential later idea:
- dependency graph;
- blast radius.

Not needed for TC1 MVP.

## AI Agent Book

Useful conceptual reference for later evaluation/agent work.

Not required for TC1 implementation.
