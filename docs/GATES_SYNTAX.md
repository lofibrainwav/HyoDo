# `.hyodo/gates.toml` field reference

Bring-Your-Own-Gates (BYOG) lets a checkout register its own quality
commands under `.hyodo/gates.toml`, and `hyodo check` runs them as
first-class gates. This page documents every field the loader
(`hyodo/gates.py`) accepts, its type, whether it is required, its default,
and the exact error `hyodo check` prints for a wrong value. Every claim below
was verified by running the loader against a broken file — see the "Source"
footer for file:line citations and the reproduction commands.

For a Node.js-flavored example and the full PASS/FAIL/SKIP/exit-code
contract, see [`onboarding-nodejs.md`](./onboarding-nodejs.md). This page is
the field-level reference; that page is the walkthrough.

## Location and schema

Path: **`.hyodo/gates.toml`**, resolved relative to the project root
`hyodo check`/`hyodo init` is pointed at.

The file is optional. If it does not exist, `load_gates_config` returns
`None` and `hyodo check` falls back to its built-in preset (or `--general`
gates) instead. If it exists but fails to parse or validate, the loader
raises `GatesConfigError` and `hyodo check` prints the error and exits `2`
("This is not a validation pass.") rather than silently running zero gates.

## Table: top level

| Field | Type | Required | Default | Meaning |
| --- | --- | --- | --- | --- |
| `schema` | string | yes | none | Must equal exactly `"hyodo.gates/v1"`. Any other value (including a missing key, which reads as `None`) is rejected. |
| `gates` | table of tables | yes | none | One sub-table per gate, keyed `[gates.<name>]`. Must be present and non-empty. |

## Table: `[gates.<name>]`

Each key under `[gates.*]` is a gate name (used as its report label) and its
value must be a TOML table with these fields:

| Field | Type | Required | Default | Meaning |
| --- | --- | --- | --- | --- |
| `pillar` | string | yes | none | One of `truth`, `goodness`, `beauty`, `benevolence`, `hyo`, `eternity`. In practice BYOG absorbs quality tools under truth/goodness/beauty — benevolence/hyo/eternity are measured natively from the checkout (`hyodo/pillars.py`) and are not meant to carry shell commands. |
| `command` | string or array of strings | yes | none | A non-empty string is split with `shlex.split`; an array is used as literal argv (no shell parsing). A leading run of POSIX `KEY=VALUE` tokens is peeled off and applied as environment overrides for that gate — this is not a separate field, it is a prefix on `command`. |
| `timeout` | integer (seconds) | no | `120` | Must be a positive `int` (a TOML boolean is rejected even though `bool` is technically an `int` subclass). Applied as the `subprocess.run(..., timeout=...)` wall-clock limit; exceeding it produces a `FAIL` (not `SKIP`) with message `"timeout"`. |

Gates always run with `shell=False` (no pipes, no shell globbing except a
constrained in-root wildcard expansion HyoDo performs itself before exec).
See `onboarding-nodejs.md` section 3 for the shell=False trap and the
PASS/FAIL/SKIP contract.

## Annotated example

```toml
schema = "hyodo.gates/v1"

# Truth: static types, absorbed from an existing mypy setup.
[gates.mypy]
pillar = "truth"
command = "mypy src"
timeout = 120

# Goodness: the project's own test suite. Array form avoids shlex parsing
# surprises when an argument itself contains spaces or shell metacharacters.
[gates.tests]
pillar = "goodness"
command = ["pytest", "-q", "tests/"]
timeout = 300

# Beauty: lint/format, with a leading KEY=VALUE env override peeled off the
# command before exec (CI=1 becomes an environment variable, not an argv
# token or the executable path).
[gates.lint]
pillar = "beauty"
command = "CI=1 ruff check ."
# timeout omitted -> defaults to 120 seconds
```

## Validation errors (verified against the loader)

Each row below was reproduced by calling `hyodo.gates.load_gates_config()`
against a `.hyodo/gates.toml` with that specific defect, run under
`PYTHONPATH=<worktree> .venv/bin/python`. The message is copied verbatim
from the exception `hyodo check` prints (prefixed with the file path).

| Defect | Example value | Error message (path prefix omitted) |
| --- | --- | --- |
| Missing/wrong `schema` | `schema = "hyodo.gates/v2"` | `unsupported schema 'hyodo.gates/v2'; expected 'hyodo.gates/v1'` |
| No `[gates]` table, or an empty one | `schema` only, or `[gates]` with no entries | `no gates defined under [gates.<name>]` |
| Gate value is not a table | `lint = "oops"` under `[gates]` | `gate 'lint' must be a table` |
| Invalid or missing `pillar` | `pillar = "speed"` | `gate 'lint' has invalid pillar 'speed'; expected one of ['beauty', 'benevolence', 'eternity', 'goodness', 'hyo', 'truth']` |
| Missing or empty `command` | `command` key absent, or `command = ""` | `gate 'lint' is missing a valid 'command' (non-empty string or array of strings)` |
| `command` is only `KEY=VALUE` tokens | `command = "FOO=bar"` | `gate 'lint' command has only env assignments; missing executable after them` |
| Invalid `timeout` (non-int, `<= 0`, or a bool) | `timeout = "60"`, `timeout = 0`, `timeout = true` | `gate 'lint' has invalid timeout <repr of the bad value>` |
| Malformed TOML syntax | unterminated string, bad table header, etc. | `invalid TOML: <underlying tomllib.TOMLDecodeError text>` |
| File exists but cannot be read (permissions, etc.) | n/a | `could not read file: <OSError text>` |

`hyodo check` surfaces any of these as `[red]<message>[/red]` followed by
`This is not a validation pass.` and exits with status `2`.

## Source

- Schema id, valid pillars, default timeout, config path constant:
  `hyodo/gates.py:59-62`
- `load_gates_config` (schema/gates-table checks, TOML/read errors):
  `hyodo/gates.py:124-158`
- `_parse_gate_spec` (`pillar`/`command`/env-prefix/`timeout` checks):
  `hyodo/gates.py:161-211`
- `hyodo check` printing the error and exiting `2`: `hyodo/cli/main.py:1701-1706`
- Reproduction: each error row above was produced by writing the noted TOML
  to a scratch `.hyodo/gates.toml` and calling
  `hyodo.gates.load_gates_config(Path("."))` directly.
