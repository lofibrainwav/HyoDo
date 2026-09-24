---
title: A worked result
description: Archival worked example from the published HyoDo 4.19.9 wheel — exact input, command, output, and exit code. It is not the current public package.
---

This is an archival worked example produced by running the published 4.19.9
package; it is not a claim about the current public package. Everything on
this page was produced by running the published package. The
output blocks are pasted from a terminal, not written by hand. Most are trimmed
to the lines under discussion; Result 1 is the one shown whole, and no line is
cut short. Two absolute paths are replaced by a placeholder — `/path/to/python`,
and the directory in front of the malformed-config error — so the page does not
encode one machine's filesystem. Nothing else was changed.

- **Package**: `hyodo` 4.19.9, installed from PyPI with
  `pipx install hyodo` into an empty pipx home.
- **Reported by the tool itself**: `HyoDo v4.19.9 - model-agnostic quality gates`,
  with `Measurement: measured by hyodo 4.19.9 (wheel)` in the pass, fail,
  empty-project and malformed-config results below.
- **Platform**: macOS. HyoDo itself ran on Python 3.14.7; the gate below ran on
  the `python` found on `PATH`, which is a separate interpreter. That
  distinction matters, and the next section says why.

The example runs locally. Installing the tools downloads packages; the gate
shown here runs your local pytest tests.

## Before you run it

Two things are easy to skip, and skipping either one changes the exit code you
get. Both were reproduced against this same 4.19.9 wheel.

**1. The gate command needs its own tool installed.** HyoDo does not supply
pytest. The gate below runs `python -m pytest`, and `python` there is resolved
from your `PATH` — not from the environment HyoDo was installed into. `pipx`
deliberately isolates HyoDo, so installing HyoDo does not put pytest anywhere.
Check the interpreter that will actually run the gate:

```bash
python -m pytest --version
```

If that fails, install it for that interpreter (`python -m pip install pytest`).
Otherwise the gate runs and reports a genuine failure that is not about your
code:

```text
  FAIL pytest (善 선 Good): /path/to/python: No module named pytest
HYODO FAIL — 1/1 gates observed, pytest
```

Exit code **1**. The gate ran; the command inside it could not.

**2. A new gate command set has to be approved once.** `.hyodo/gates.toml`
registers commands that HyoDo will execute, so HyoDo will not run an unreviewed
command set on your behalf. In a non-interactive shell it refuses and says so:

```text
  SKIP pytest (善 선 Good): gates.toml command set is new or unapproved in a
non-interactive environment -- set HYODO_GATES_TRUST_ALL=1 to pre-approve or run
`hyodo check` interactively once to review and record trust

==================================================
No user gates were executed
This is not a validation pass.
HYODO UNOBSERVED — 0/1 gates observed, required gates UNOBSERVED
```

Exit code **2**, not `0`. Run it once in a real terminal to review and approve —
that is the step shown under "The command" below. The recorded decision lives in
`.hyodo/gates-trust.json` in your project, and changing a command invalidates it.

## The input

Two Python files and one HyoDo config make up the example input.

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

The first time, HyoDo shows the command set it is about to run and waits. This
is the approval from "Before you run it", verbatim:

```text
HyoDo Bring-Your-Own-Gates: .hyodo/gates.toml command set changed or is new.
  [goodness] pytest: python -m pytest tests -q
  fingerprint: 2be698af424180e66492c8c54c1481b507789c2ea7a7f05c177ae044c8bd7ca0
Trust and run this command set now? [y/N] y
```

The fingerprint covers the commands, not your source or its location, so editing
`pricing.py` does not re-prompt but editing the gate command does. It is also the
same value for anyone running this exact gate set on this version of HyoDo: if
you copied the config above, the fingerprint you are asked to approve should
match the one printed here, character for character. A matching fingerprint says
the command text matches. It says nothing about what that command resolves to on
your machine — the interpreter, the installed packages, your project's code and
the result are all still yours, which is why the prerequisites above matter.
Answering `y` records the decision and the run continues. With this command set
unchanged, later runs reuse the recorded approval.

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

Read the approval reminder carefully: *"Gates support review readiness. Human
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

This is the result worth showing on purpose, because an empty run is the easiest
one to misread as success. Run the same command in a directory with no gates and
no recognizable project:

```text
No project gates were executed
This is not a validation pass.
Measurement: measured by hyodo 4.19.9 (wheel)
HYODO UNOBSERVED — 0/0 gates observed, required gates UNOBSERVED; Sampled syntax gates only (up to 50 files per language); not a full-project validation
```

Exit code **2**.

Not `0`. An empty run is not a pass. Note what the verdict line carries with it:
with no `.hyodo/gates.toml` to read, HyoDo falls back to built-in sampled syntax
gates, and it says so in the same breath as the verdict — sampled, not a
full-project validation.

A broken config arrives at the same verdict by a different route, and without
the sampled-gates fallback, because there is a config and HyoDo refuses to guess
what it meant. During the making of this page an early draft omitted the
`schema` key, and the real output was:

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
