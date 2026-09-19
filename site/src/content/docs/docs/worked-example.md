---
title: A worked result
description: One complete HyoDo run on a three-file project — the exact input, the exact command, the verbatim output, and the exit code, produced by the published 4.19.9 wheel.
---

Everything on this page was produced by running the published package. The
output blocks are pasted from a terminal, not written by hand.

- **Package**: `hyodo` 4.19.9, installed from PyPI with
  `pipx install hyodo` into an empty pipx home.
- **Reported by the tool itself**: `HyoDo v4.19.9 - model-agnostic quality gates`,
  and every result line below ends with `measured by hyodo 4.19.9 (wheel)`.
- **Platform**: macOS, Python 3.14.7.

You can reproduce it in about a minute. Nothing leaves your machine.

## The input

Three files, plus one HyoDo config. This is the whole project.

`src/pricing.py`

```python
def apply_discount(cents: int, percent: int) -> int:
    """Return the price after a percentage discount."""
    return cents - (cents * percent // 100)
```

`tests/test_pricing.py`

```python
from src.pricing import apply_discount


def test_full_price():
    assert apply_discount(1000, 0) == 1000


def test_half_off():
    assert apply_discount(1000, 50) == 500


def test_free():
    assert apply_discount(1000, 100) == 0
```

`.hyodo/gates.toml` — this is the Bring-Your-Own-Gates file. HyoDo does not
supply the test runner; it runs the command you already use.

```toml
schema = "hyodo.gates/v1"

[gates.pytest]
pillar = "goodness"
command = ["python", "-m", "pytest", "tests", "-q"]
timeout = 120
```

## The command

```bash
hyodo check
```

## Result 1 — the gate passes

```text
╭──────────────────────────╮
│ HyoDo Code Quality Check │
╰──────────────────────────╯
Target: /tmp/demo
User gates: /tmp/demo/.hyodo/gates.toml
  PASS pytest (善 선 Good): ok

==================================================
All executed gates passed (1/1 gates ran)
Gates support review readiness. Human approval still required.
Measurement: measured by hyodo 4.19.9 (wheel)
HYODO PASS — 1/1 gates observed, all executed gates passed
```

Exit code **0**.

Read the second-to-last line carefully: *"Gates support review readiness. Human
approval still required."* A pass is evidence that the gates you registered ran
and succeeded. It is not approval to merge or deploy. That is the whole product
boundary in one line of output.

## Result 2 — a real bug, caught

Change one line of `src/pricing.py` to a units mistake — subtracting `percent`
dollars instead of a percentage:

```python
    return cents - percent * 100
```

Same command, no other change:

```text
FAILED tests/test_pricing.py::test_half_off - assert -4000 == 500
FAILED tests/test_pricing.py::test_free - assert -9000 == 0
2 failed, 1 passed in 0.10s

==================================================
Some gates failed (1/1 gates ran)
Failure details:
  - pytest: test summary info ============================
FAILED tests/test_pricing.py::test_half_off - assert -4000 == 500
FAILED tests/test_pricing.py::test_free - assert -9000 == 0
2 failed, 1 passed in 0.10s
Next action: fix the listed gate(s) and re-run hyodo check.
Measurement: measured by hyodo 4.19.9 (wheel)
HYODO FAIL — 1/1 gates observed, pytest
```

Exit code **1**. Note `1/1 gates observed` — the count of what actually ran is
reported next to the verdict, so a verdict can never quietly rest on zero
measurements.

## Result 3 — nothing was measured, and it says so

This is the result most tools get wrong, so it is worth showing on purpose.
Run the same command in a directory with no gates and no recognizable project:

```text
Measurement: measured by hyodo 4.19.9 (wheel)
HYODO UNOBSERVED — 0/0 gates observed, required gates UNOBSERVED
```

Exit code **2**.

Not `0`. An empty run is not a pass. The same thing happens if
`.hyodo/gates.toml` exists but is malformed — during the making of this page an
early draft of the config omitted the `schema` key, and the real output was:

```text
.hyodo/gates.toml: unsupported schema None; expected 'hyodo.gates/v1'
This is not a validation pass.
Measurement: measured by hyodo 4.19.9 (wheel)
HYODO UNOBSERVED — 0/0 gates observed, required gates UNOBSERVED
```

Also exit `2`. A broken config is reported as *not measured*, never as green.

## The three exit codes, asserted

Run against the published 4.19.9 wheel:

| Situation | Exit code |
| --- | --- |
| Registered gates ran and passed | `0` |
| A registered gate failed | `1` |
| Nothing ran, or the config was unreadable | `2` |

## What this result does not show

- It does not show that your project is correct. It shows that the commands you
  registered ran, and what they returned.
- It does not authorize a merge or a deployment. HyoDo produces evidence; the
  decision stays with you or your host.
- One gate on a three-file project is deliberately small. A larger project
  registers more gates; the report grows, and the contract above does not change.
- The pass here says nothing about the two tests that were never written. HyoDo
  reports what was measured, not what was omitted.

## Next

- [Quickstart](/docs/quickstart/) — the same steps on your own project.
- [Gate syntax reference](https://github.com/lofibrainwav/HyoDo/blob/v4.19.9/docs/GATES_SYNTAX.md)
  — every field `.hyodo/gates.toml` accepts, and the exact error for a wrong value.
- [Product boundary](/docs/product-boundary/) — what HyoDo owns and what the host owns.
