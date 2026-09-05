# Integration Surface Research — 2026-09-05

## Status

Recovered decision notes from the implementation-surface research lane. This is
research evidence, not proof that any integration below has shipped.

## Directional finding

For repository-local gate tools, the strongest adoption surfaces are the places
developers already enforce code quality:

1. pre-commit hooks for local feedback,
2. CI checks for enforcement,
3. SARIF or equivalent platform-native findings for visibility,
4. a thin GitHub Action wrapper for copy-paste adoption.

HyoDo already has the CLI primitives needed for these surfaces. The research
therefore favors thin adapters over a new policy engine or hosted dashboard.

## Recommended order

### 1. pre-commit hook

Expose `hyodo safe --strict` as the first hook. Keep repository-level scanning
serial and avoid pretending the hook replaces CI.

A slower `hyodo check` hook can be offered later as a manual or pre-push stage.

### 2. SARIF output

Map `hyodo safe` findings into SARIF so repository hosts can display findings in
their native security interface. Preserve rule id, severity, file, and line
information where available.

### 3. Composite GitHub Action

Keep the Action thin: install HyoDo, run the existing CLI, and optionally upload
SARIF. The Action should reuse CLI exit contracts instead of adding a second
policy implementation.

### 4. Starter workflow and documentation

After the hook, SARIF, and Action exist, provide a minimal starter workflow and
copy-paste examples. Documentation should describe actual shipped surfaces, not
research intentions.

## Dependency-stability note

Fast-moving SDKs should remain outside the core model. HyoDo's existing MCP
strategy—optional extra, compatibility shim, and CI coverage across supported
major versions—is the pattern to preserve.

If OpenTelemetry GenAI export is added later, keep vocabulary mapping behind one
adapter and optional dependency until the semantic conventions are stable enough
to treat as a durable public contract.

## Explicitly deferred

- editor extensions,
- hosted dashboards,
- broad telemetry export,
- any integration whose maintenance cost exceeds its demonstrated adoption
  value.

These remain hypotheses until measured against actual user adoption.
