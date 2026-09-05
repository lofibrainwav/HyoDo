# Onboarding and Terminology UX Research — 2026-09-05

## Status

Recovered decision notes from the onboarding and terminology research lane.
These recommendations are hypotheses to validate against user behavior; they
are not release claims.

## Core finding

An unusual brand name can be memorable without hurting adoption. Friction rises
when users must understand the brand's metaphor or philosophy to operate the
tool.

For HyoDo, keep the brand and fail-closed philosophy, but lead machine-adjacent
interfaces with standard engineering language.

## Recommended interface pattern

Use technical labels first and philosophy second:

- Type safety (Truth)
- Tests and safety (Goodness)
- Lint and format (Beauty)
- Public surface (Benevolence)
- Data consent (Hyo)
- Audit continuity (Yeong)

The parenthetical labels are optional context. Exit codes, JSON keys, and the
first line of help output should remain neutral and immediately understandable.

## Progressive disclosure

The top-level CLI should prioritize daily commands and group advanced surfaces.
A useful target is:

```text
safe  init  check  score  dashboard  start  report  version
event  policy  schema  mcp
```

Less common or legacy names can remain as documented aliases or hidden commands
when compatibility requires them.

## Onboarding hypothesis

`hyodo start` is the best candidate for a guided first-run flow because it can
inspect the repository, point to `safe`, offer `init`, and print the next
commands. Human prompts should always have non-interactive flag equivalents for
CI and scripts.

Every error path should make the next useful action obvious. A concise pattern
is:

```text
New here? Run: hyodo start
No-setup scan: hyodo safe
```

## Documentation rule

README and package metadata should lead with practical behavior. The complete
six-dimension philosophy belongs in `PHILOSOPHY.md` and deeper documentation.
The phrase "unobserved is never green" is useful because it directly describes
an engineering behavior rather than requiring cultural context.

## What not to change without evidence

- Do not rename HyoDo solely because the name is unusual.
- Do not remove the philosophy from the project identity.
- Do not change stable JSON keys or CLI commands merely to make documentation
  look simpler.
- Do not hide advanced functionality until compatibility and discoverability
  are tested.

The next step is to validate these changes with actual onboarding tasks and CLI
usage, not to treat the research note as a mandate.
