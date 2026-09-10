# Accessibility receipt — virtue accent contrast, 2026-09-10

A record of one defect, how it was measured, and what now prevents it from
coming back. Written because the test suite was green while the defect was
shipping, and that gap is worth a receipt rather than a changelog line.

## The gap

At `d1e6284` (HyoDo 4.19.0, released), the suite reported 1291 passed,
1 skipped. Ruff was clean. Pyright reported zero errors. Every gate in CI
was green.

All six virtue accents were nonetheless below WCAG AA as text.

```
test suite GREEN + known accessibility defect + no regression oracle
= false green
```

The colour tests that existed asserted that `hyodo/dashboard.py` and
`site/src/styles/tokens.css` agreed on the hex values and that the columns
appeared in a fixed order. Both held. They held at values that failed
contrast, in both files, consistently. Agreement is not correctness: two
files can be in perfect sync and both wrong.

## What was measured

The accents are rendered as text in three places — `h2 span` and
`.reference` on the dashboard cards, `.grid-colhead h2 span` in the graph
viewer — so WCAG AA (4.5:1) applies. Ratios computed against the surfaces
those elements are actually printed on, not against the page background:

| virtue | hex at `d1e6284` | light card `#fffdf7` | dark card `#1d1d1a` |
|---|---|---|---|
| Truth | `#2563eb` | 5.08 | **3.66** |
| Goodness | `#059669` | **3.70** | 5.02 |
| Beauty | `#7c3aed` | 5.60 | **3.32** |
| Benevolence | `#ea580c` | **3.50** | 5.31 |
| Hyo | `#ca8a04` | **2.89** | 6.43 |
| Eternity | `#4f46e5` | 6.18 | **3.01** |

Six of six failed on one theme or the other. Hyo on the light card, at
2.89:1, was the worst.

## What changed

Each virtue now carries two values. This is arithmetic, not preference: no
single hex clears 4.5:1 against both a near-white card and a near-black
one. Three virtues keep their existing hex as the light value and two keep
theirs as the dark value, so the palette's identity survives.

Accent and card surface are switched by the same `prefers-color-scheme`
media query. An earlier revision drove the accent from `light-dark()` while
the surface stayed on the media query. The two read different signals, and
forcing `color-scheme` in the browser rendered a dark accent on the light
card at 2.89:1 — the original defect, reintroduced by a mechanism mismatch
rather than by a wrong colour. One mechanism means the two cannot disagree.

The graph viewer baked a hex into a `style` attribute, where no media query
can reach it. It now takes the same accent class the cards use.

## What prevents the regression

The palette is the smaller half of this change. The oracle is the point.

1. **Surfaces are parsed, not restated.** The contrast test reads the
   `--surface` declarations out of `hyodo/dashboard.py`. Changing a card
   colour re-runs the computation instead of quietly invalidating a number
   copied into a test file.
2. **Themes are separated by the browser's own signal** — whether a
   declaration sits inside the dark media query — so the test and the
   renderer classify light and dark the same way.
3. **A negative fixture proves the oracle discriminates.** It feeds the
   real accents a mid-grey surface and asserts that every virtue fails. A
   contrast function that always returns a passing number is caught there
   before the real check goes quietly green.
4. **The two-value split is asserted to stay load-bearing**, so it cannot
   be collapsed back to one colour without a deliberate decision.
5. **The WCAG arithmetic is anchored** against known values (black on white
   is 21.0; three-digit hex must expand, since one card surface is written
   `#fff`), so the gate cannot drift along with the palette it guards.

## Verification

| check | result |
|---|---|
| `pytest tests` | 1295 passed, 1 skipped |
| `ruff check` / `ruff format --check` | clean |
| `pyright hyodo` | 0 errors, 0 warnings |
| CI | 15/15 |
| browser readback, light theme | worst 4.62:1 |
| browser readback, dark theme | worst 4.60:1 |

The browser figures are measured on the rendered DOM: the computed colour
of each accent element against its resolved card background, with the dark
media query activated. They are a readback, not a restatement of the values
in the diff — the two were compared and agree.

## Scope

This receipt covers the six virtue accents as text. It does not claim a
WCAG audit of the dashboard. Two things are explicitly outside it:

- The ring-item `--tint` keeps an inline value, because those colours are
  arbitrary per entry. It renders as a fill and a 3px border, never as
  text, so AA does not bind — but it is also not covered by the gate above.
- `.grid-colhead` draws its top border from `var(--accent, #888)` while
  `--accent` is set on the child `h2`, so that border has always fallen
  back to grey rather than showing the virtue colour. That is a separate
  finding, left alone here rather than folded into an accessibility change.

## Lineage

Supersedes PR #233, which patched the pre-redesign dashboard stylesheet.
`main` replaced that stylesheet wholesale in #234 and #235, leaving #233
unrebaseable: taking `main`'s side dropped the contrast fix, taking #233's
side reverted the redesign. Its finding is preserved here; its CSS is not.

HyoDo 4.19.0 was a correct release. The package, the CLI, the gates and the
Evidence Pack lineage were all green and remain so. Product quality is a
different axis from release completion, and on that axis this defect was
open until now. Keeping the two apart is the point of writing it down.
