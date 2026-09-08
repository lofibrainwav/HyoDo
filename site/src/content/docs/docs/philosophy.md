---
title: Philosophy → Math → Code
description: Why HyoDo exists, the six virtues it measures, the geometric mean that makes the signal fail-closed, and the exit codes that carry it into practice.
---

## 1. Why this exists

> I cannot read code. So when an AI told me 'it is done', I had no way to
> know whether that was true. I believe friction in the world can be
> measured. The six virtues are six axes of that friction, and the
> geometric mean is the honest mathematics that says: if any one axis is
> zero, the whole is zero. HyoDo carries that mathematics into an exit
> code. It speaks only about what it observed, and it never shows a green
> light for what it did not observe. It moves on its own exactly as far as
> the trust you have given it, and it leaves a receipt for every step it
> took. The Kingdom is my own operating system; HyoDo is meant to be a
> digital wheelchair for everyone who cannot read the code.

## 2. Six virtues

| Pillar | KO / Hanja | Technical meaning | Evidence |
| --- | --- | --- | --- |
| Truth | 진 / 眞 | Type / static correctness | Command gate |
| Goodness | 선 / 善 | Tests + safety stability | Command gate + `safe` |
| Beauty | 미 / 美 | Lint / format | Command gate |
| Benevolence | 인 / 仁 | Public-surface integrity | Native AST |
| Hyo | 효 / 孝 | Consent + data protection | Native AST |
| Yeong | 영 / 永 | Continuity of measurement | history ledger |

Command gates (Truth, Goodness, Beauty) run tools the project already owns —
`hyodo init` absorbs them into `.hyodo/gates.toml`. Native collectors
(Benevolence, Hyo, Yeong) are never replaced by a shell command; when they
are unavailable, they are reported as "Not measured," not silently skipped.

### Public score naming

- **Public name:** HyoDo Integrity Score.
- **Model:** Six-Virtue Model.
- **Subset:** Trinity Gates.
- **Formula lineage:** HYOGOOK V5.

The name is the operator-facing label. `HYOGOOK V5` remains the formula
lineage needed for reproducibility, not a competing public product name.

## 3. The mathematics

Optional `hyodo score` combines five pillar scores with a **geometric mean**,
not an arithmetic one. The difference matters: an arithmetic mean of
(structure=1.0, security=0.0) still comes out to 0.5, which looks "ok." A
geometric mean with any zero axis collapses to 0 — the whole signal fails.

> **Fail-closed:** one pillar at 0 fails the whole review signal.

That rule is implemented directly, not just claimed. From
`hyodo/__init__.py`:

```python
def calculate_geometric_mean(values: list[float]) -> float:
    """Calculate geometric mean for Eternity pillar.

    S = ⁵√(T × G × In × B × C)

    Args:
        values: List of 5 pillar scores (0-1 or 1-10 scale)

    Returns:
        Geometric mean using the same scale as the input values.
    """
```

`--partial` allows missing pillars and adds `SIGNAL_CONFIDENCE_WEAK`. It
does not invent a strong signal via a silent fill-in of 1.0 for whatever was
not measured.

### Deriving the five inputs (`hyodo score --from-check`)

`hyodo score` normally requires the caller to supply all five pillar
values by hand. `hyodo score --from-check [--root R] [--json]` derives
those same five inputs instead, in-process (no subprocess calls), from
what `hyodo check`, `hyodo safe`, and the test-integrity scan already
observed about a checkout. `hyodo/score_derive.py` defines a literal
`PILLAR_RULE_TABLE` (`rule_id -> pillar + max weight`) so every number has
a named source, and each pillar reports its own coverage —
`OBSERVED` / `PARTIAL` / `UNOBSERVED` — alongside its value. An
`UNOBSERVED` pillar reports `None`, never a smuggled 0 or 100, and is
excluded from the Eternity geometric-mean term rather than defaulted; when
any pillar is `UNOBSERVED`, the command withholds the combined TOTAL score
and names which pillar(s) still need an explicit `--benevolence 0.8`-style
flag to complete it. The HyoDo Integrity Score formula itself is unchanged
by `--from-check` — it only proposes inputs — and the command still prints
"review signal, not automatic approval." See `docs/SCORE_DERIVATION.md`
for the full rule table and a calibration run.

## 4. The code

The mathematics above is what an optional review score does. The exit codes
below are what every HyoDo command does, always, whether or not scoring is
in use:

| Command | Contract |
| --- | --- |
| `safe` | `0` report · `1` strict high finding · `2` bad path |
| `check` | `0` executed gates passed · `1` gate failed · `2` none/malformed |
| `event` / `policy` | `0` valid/ALLOW · `1` invalid/DENY · `2` unobserved · `3` ASK |
| `schema check` | `0` valid · `1` validation error · `2` unobserved input |

The policy gate speaks in four decision words, documented directly in
`hyodo/policy.py`:

```python
"""Local policy gate for agent events (FDE Evidence Spine).

Policy is loadable from ``.hyodo/policy.toml`` (schema ``hyodo.policy/v1``).
Missing or malformed policy is **unobserved**, never silent ALLOW.

HyoDo emits a decision object; the agent runtime must enforce DENY.
"""

decision: str  # ALLOW | DENY | ASK | UNOBSERVED
```

`ASK` is now emitted when policy evaluation observes an external variable that
needs an operator decision. `ALLOW`, `DENY`, and `UNOBSERVED` remain live, and
trust grants are capped by the tracked policy configuration. See the
[Roadmap](/docs/roadmap/) for the 4.13.0 development cycle.

## Next

- [Quickstart](/docs/quickstart/)
- [Roadmap](/docs/roadmap/)
- [Trust](/docs/trust/)
