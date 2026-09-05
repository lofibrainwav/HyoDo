# Mutation Automation V1

## Goal

Turn the manual mutation receipt into repeatable CI evidence without inventing a
blocking threshold before a real baseline exists.

## Tier 1 — pull-request scoring evidence

`cosmic-ray.scoring.toml` mutates the scoring core in `hyodo/__init__.py` and
runs the focused scoring suites. Pull requests that touch mutation-relevant
surfaces execute this lane automatically.

The lane records:

- baseline success,
- Cosmic Ray session database,
- survival-rate output,
- text report,
- XML report.

The first measured rate is advisory. It becomes a gate only after review.

## Tier 2 — full-core evidence

The existing `cosmic-ray.toml` targets the four core modules captured in the
mutation receipt. A weekly schedule and explicit workflow dispatch run the full
session because Cosmic Ray's local distributor executes mutations sequentially.

The full-core lane is also advisory in v1.

## Fail-closed rule

A workflow execution failure, missing receipt, failed baseline, or incomplete
report is not a passing mutation score. The workflow may be advisory about the
survival-rate threshold, but it must still fail when the measurement itself
cannot be completed.

## Promotion rule

A later change may add `cr-rate --fail-over <threshold>` only after:

1. at least one clean scoring run is recorded,
2. the surviving mutants are reviewed for equivalent or untestable cases,
3. the threshold and exceptions are documented,
4. the same command can be reproduced locally.
