"""Separate what ``hyodo check`` executed from what a reader may conclude.

4.20 reported one word per run, derived from the process exit code: ``0`` ->
``PASS``, ``1`` -> ``FAIL``, anything else -> ``UNOBSERVED``. That word answers
"did an executed gate fail?" but it was read as "was this checkout verified?".
Those are two different questions the moment a gate is *declared* and then not
executed -- a missing binary, an unapproved command set, a measuring HyoDo that
cannot be tied to the code under measurement. One PASS plus one SKIP printed
``HYODO PASS``.

This module adds the missing axis without touching the old one. The exit code
and the JSON ``status`` key keep their 4.20 meanings byte-for-byte; beside them
now sit:

``coverage``   ``FULL`` | ``PARTIAL`` | ``NONE`` -- was every declared gate executed?
``complete``   ``coverage == FULL``
``effective``  ``PASS`` | ``FAIL`` | ``UNOBSERVED`` -- what the run supports concluding

``effective`` is the conservative combination: a legacy ``PASS`` survives only
when coverage is ``FULL`` *and* the measuring HyoDo was itself ``OBSERVED``.
Nothing here can turn an observed failure into a pass, and nothing here changes
an exit code.
"""

from __future__ import annotations

COVERAGE_FULL = "FULL"
COVERAGE_PARTIAL = "PARTIAL"
COVERAGE_NONE = "NONE"

EFFECTIVE_PASS = "PASS"
EFFECTIVE_FAIL = "FAIL"
EFFECTIVE_UNOBSERVED = "UNOBSERVED"


def gate_coverage(observed: int, expected: int) -> str:
    """Classify how much of the declared gate set actually executed.

    ``expected`` is what the run said it would measure, ``observed`` is what
    produced a real PASS/FAIL outcome. A SKIP (missing tool, refused command
    set) is declared-but-not-executed and therefore lowers coverage.
    """
    if expected <= 0 or observed <= 0:
        return COVERAGE_NONE
    if observed == expected:
        return COVERAGE_FULL
    if observed > expected:
        return COVERAGE_NONE
    return COVERAGE_PARTIAL


def effective_status(
    legacy_status: str,
    coverage: str,
    provenance_validity: str | None = None,
) -> str:
    """Return what the run supports concluding, given the legacy verdict.

    An observed failure stays a failure: incomplete coverage never softens a
    ``FAIL`` into "we could not see". Only a ``PASS`` can be downgraded, and
    only to ``UNOBSERVED``.
    """
    if legacy_status == EFFECTIVE_FAIL:
        return EFFECTIVE_FAIL
    if legacy_status != EFFECTIVE_PASS:
        return EFFECTIVE_UNOBSERVED
    if provenance_validity is not None and provenance_validity != "OBSERVED":
        return EFFECTIVE_UNOBSERVED
    if coverage != COVERAGE_FULL:
        return EFFECTIVE_UNOBSERVED
    return EFFECTIVE_PASS


def coverage_detail(observed: int, expected: int, coverage: str) -> str | None:
    """Explain a non-FULL coverage in the reader's terms, else ``None``.

    Says how many declared gates went unexecuted rather than only printing a
    ratio, so "1/2" cannot be skimmed as a rounding detail.
    """
    if coverage == COVERAGE_FULL:
        return None
    if coverage == COVERAGE_NONE:
        return "no declared gate was executed (coverage NONE)"
    return (
        f"{expected - observed} of {expected} declared gate(s) were not executed (coverage PARTIAL)"
    )
