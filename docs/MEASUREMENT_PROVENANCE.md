# Measurement provenance (`hyodo.measurement-provenance/v1`)

A PASS proves nothing until you know what produced it. This contract records
which HyoDo measured which target, from where, and whether that measurement is
valid at all.

## Why it exists

On 2026-09-10 a virtualenv inside one HyoDo checkout resolved its editable
install to a *different* HyoDo checkout. `hyodo check` measured this
repository's files with the other repository's gate code. Both reported
`v4.19.0`. Nothing in any output distinguished them.

That is a false green of a specific kind: the gates ran, the gates passed, and
the result described code nobody asked about.

## A separate axis from policy

```
policy      ALLOW / DENY / ASK / UNOBSERVED
provenance  OBSERVED / MISMATCH / UNOBSERVED
```

Policy answers *what an actor was permitted to do*. Provenance answers *whether
this measurement is valid at all*. Reusing `ASK` for "the measuring code was
wrong" would collapse two unrelated questions into one unreadable field, so the
two vocabularies stay disjoint. A host that wants human intervention can route
`MISMATCH` or `UNOBSERVED` to a person; HyoDo does not presume that for it.

## Relations

| relation | meaning | validity |
|---|---|---|
| `EXTERNAL_TARGET` | an installed HyoDo measuring another project | `OBSERVED` |
| `SELF_SAME_CHECKOUT` | HyoDo measuring itself with its own code | `OBSERVED` |
| `SELF_OTHER_CHECKOUT` | HyoDo measuring itself with code from elsewhere | `MISMATCH` |
| `SOURCE_UNOBSERVED` | self-measurement whose sources cannot be compared | `UNOBSERVED` |

`EXTERNAL_TARGET` is the ordinary, intended shape of this tool. A naive rule
like "package root differs from target root, therefore complain" would flag
every legitimate use; the relation is classified first, and only
self-measurement can mismatch.

**Version is not an input to that classification.** Two builds can carry the
same version string and differ in every line — that is exactly how the original
accident stayed invisible. Equal versions never prove equal sources here.
Equal commits do not either when the tree is dirty, because a commit id
under-describes a directory with uncommitted edits; that case degrades to
`SOURCE_UNOBSERVED` rather than claiming a match it cannot support.

## Effect on a verdict

- `MISMATCH` — never green. `hyodo check` downgrades a `PASS` to `UNOBSERVED`
  and the dashboard prints a banner above the gate cards.
- `UNOBSERVED` — never *silently* green. The state is always printed.
- `OBSERVED` — recorded, no effect on any gate.

The provenance line is emitted whether or not anything is wrong, so
"measured by what?" always has an answer.

## Fields

Always recorded: `tool_name`, `tool_version`, package origin, Python
interpreter, target root, tool source commit, target commit, dirty flags for
both, `install_mode` (`editable` / `wheel` / `source` / `unknown`), `relation`,
`validity`.

## Two views, for privacy

An absolute path carries a username.

- `to_local_dict()` keeps full paths. It is for the terminal in front of the
  person who needs to know which directory to go fix.
- `to_portable_dict()` is what travels: commit ids, install mode, relation,
  and truncated SHA-256 digests of the paths. Two receipts can still be
  compared for "same place or not" without publishing anyone's home directory.

`hyodo check --json` and `GET /api/evidence` both carry the portable form,
because both get pasted into issues. The human-readable terminal line and the
dashboard's `TARGET //` header carry paths, because they do not leave the
machine.

## Reading it

```console
$ hyodo check
Measurement: self-measured from this checkout (source)
HYODO PASS — 4/4 gates observed, all executed gates passed
```

```console
$ hyodo check
Measurement: MEASUREMENT MISMATCH: target 814f6fb7 was measured by hyodo from
/Users/…/HyoDo-release at e8e1193c — same version string, different code
HYODO UNOBSERVED — 4/4 gates observed, …
```

The verdict line stays last, because that is the line callers parse.
