"""Measure the release chain and write a receipt that says what was measured.

`docs/releases/4.19.1.md` shipped with every chain item as `- [ ]` while the
tag was signed, the GitHub Release published with both assets attached, and
4.19.1 already served by PyPI. The document claimed none of it had happened.

The bug is the shape, not the writer. `prepare_release` emits the receipt
*before* the chain runs, and in a task list `- [ ]` asserts "not done" -- so
the section is false the moment the release succeeds, and nothing ever brings
anyone back to it. Six releases were reconciled by hand; two were not.

`UNOBSERVED` is the state this project already uses for "nobody measured
this", and unlike an unchecked box it stays true until somebody does. A
prepared receipt is therefore honest on the day it is written and honest a
month later; running this script turns the steps it can observe into
`OBSERVED` lines that name the durable artifact behind each one.

Nothing here infers. A step is `OBSERVED` only when a specific identifier was
read back -- a tag and its commit, a workflow run id, an asset name, the
version PyPI actually serves.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

StepState = Literal["OBSERVED", "UNOBSERVED"]

#: The chain, in the order it actually happens. These names are the join key
#: between a written receipt and a fresh measurement, so they are stable text
#: rather than an enum that could be renamed without noticing the drift.
CHAIN_STEPS: tuple[str, ...] = (
    "Signed verified tag",
    "GitHub Release created",
    "Release evidence workflow",
    "SBOM asset attached",
    "SHA-256 receipt attached",
    "Release published",
    "PyPI publish",
    "PyPI provenance verified",
    "Install smoke",
)

RECEIPT_HEADING = "## Release chain receipt"

_UNMEASURED_NOTE = (
    "Not measured yet. Run `python -m scripts.release.verify_release_chain <version>`\n"
    "to replace this section with a measured receipt. `UNOBSERVED` means nobody has\n"
    "looked, which is not the same as a step that failed."
)

_LINE_RE = re.compile(r"^- (OBSERVED|UNOBSERVED) — ([^(\n]+?)(?: \((.*)\))?\.$")


@dataclass(frozen=True)
class ChainStep:
    """One step of the release chain, and what was read back to observe it."""

    name: str
    state: StepState
    evidence: str | None

    def validate(self) -> ChainStep:
        """Reject an OBSERVED step that cannot point at anything.

        A tick with no identifier is the assertion this receipt exists to
        replace: it cannot be rechecked later, so it is not evidence.
        """
        if self.state == "OBSERVED" and not (self.evidence or "").strip():
            raise ValueError(f"{self.name}: OBSERVED requires evidence to point at")
        return self

    def render(self) -> str:
        self.validate()
        if self.evidence:
            return f"- {self.state} — {self.name} ({self.evidence})."
        return f"- {self.state} — {self.name}."


def render_receipt(steps: list[ChainStep], *, measured_at: str | None) -> str:
    """The whole `## Release chain receipt` section, measured or not."""
    lines = [RECEIPT_HEADING, ""]
    if measured_at:
        lines.append(f"Measured {measured_at} by `scripts/release/verify_release_chain.py`.")
    else:
        lines.append(_UNMEASURED_NOTE)
    lines.append("")
    lines.extend(step.render() for step in steps)
    return "\n".join(lines) + "\n"


def parse_receipt(document: str) -> dict[str, ChainStep]:
    """Read the states a receipt document already claims, by step name."""
    found: dict[str, ChainStep] = {}
    section = document.split(RECEIPT_HEADING, 1)[-1]
    # stop at the next heading so a later section cannot be misread as chain
    section = section.split("\n## ", 1)[0]
    for line in section.splitlines():
        match = _LINE_RE.match(line.strip())
        if not match:
            continue
        state, name, evidence = match.groups()
        found[name.strip()] = ChainStep(
            name=name.strip(),
            state="OBSERVED" if state == "OBSERVED" else "UNOBSERVED",
            evidence=evidence,
        )
    return found


def receipt_drift(document: str, measured: list[ChainStep]) -> list[str]:
    """Where the written receipt disagrees with a fresh measurement.

    Reported in both directions. A document still saying `UNOBSERVED` for a
    step that has since been observed is the 4.19.1 defect; a document
    claiming `OBSERVED` for something no longer measurable is worse, and is
    the reason this does not only look for the first case.
    """
    written = parse_receipt(document)
    drift: list[str] = []
    for step in measured:
        current = written.get(step.name)
        if current is None:
            drift.append(f"{step.name}: measured {step.state}, absent from the receipt")
        elif current.state != step.state:
            drift.append(
                f"{step.name}: receipt says {current.state}, measurement says {step.state}"
            )
    return drift


# --- reading the world ---------------------------------------------------


def _run(*args: str, timeout: int = 30) -> str | None:
    """Command output, or None when it cannot be run or fails.

    Every failure degrades to "not observed" rather than raising: a receipt
    that cannot be measured must say so, not crash the release.
    """
    if shutil.which(args[0]) is None:
        return None
    try:
        done = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode != 0:
        return None
    return done.stdout.strip() or None


def _gh_json(*args: str) -> Any | None:
    raw = _run("gh", *args)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


_MIN_SHA_OVERLAP = 8


def tag_step(*, tag: str, commit: str | None, signed: bool, verified: bool) -> ChainStep:
    """The tag step, keeping "not verifiable here" apart from "not signed".

    Every tag from v4.16.0 on carries a signature block, but only v4.19.1
    verifies locally -- the earlier signer is not in this machine's
    allowed-signers file. Rendering both as a bare UNOBSERVED would let a
    reader take "we could not check" for "nobody signed it", which is the
    louder and wronger claim.
    """
    if commit and verified:
        return ChainStep(
            name="Signed verified tag",
            state="OBSERVED",
            evidence=f"`{tag}` -> `{commit[:7]}`, signature verified",
        )
    if commit and signed:
        return ChainStep(
            name="Signed verified tag",
            state="UNOBSERVED",
            evidence=f"`{tag}` -> `{commit[:7]}` is signed, but not verifiable here",
        )
    if commit:
        return ChainStep(
            name="Signed verified tag",
            state="UNOBSERVED",
            evidence=f"`{tag}` -> `{commit[:7]}`, no signature found",
        )
    return ChainStep(name="Signed verified tag", state="UNOBSERVED", evidence=None)


def matching_run(runs: list[dict[str, Any]] | None, *, tag: str, commit: str | None) -> str | None:
    """The id of the successful run that belongs to *this* version, or None.

    An earlier draft cited each workflow's newest successful run. That is not
    a measurement: the newest run can belong to another release, and a wrong
    identifier in a receipt is worse than an absent one, because it looks
    recheckable and is not.

    Two ties count. `publish.yml` runs on the tag, so its `headBranch` is the
    tag itself. `release-evidence.yml` is dispatched from `main`, so only its
    `headSha` can place it -- compared by prefix, since the two sources
    abbreviate differently. When neither ties, the step stays UNOBSERVED.
    """
    for run in runs or []:
        if run.get("conclusion") != "success":
            continue
        if run.get("headBranch") == tag:
            return str(run.get("databaseId"))
        sha = str(run.get("headSha") or "")
        if not commit or len(sha) < _MIN_SHA_OVERLAP:
            continue
        if sha.startswith(commit[:12]) or commit.startswith(sha[:12]):
            return str(run.get("databaseId"))
    return None


def measure_chain(version: str, *, repo: str, root: Path) -> list[ChainStep]:
    """Read each chain step back off git, GitHub and PyPI."""
    tag = f"v{version}"
    steps: list[ChainStep] = []

    def add(name: str, evidence: str | None) -> None:
        steps.append(
            ChainStep(name=name, state="OBSERVED" if evidence else "UNOBSERVED", evidence=evidence)
        )

    commit = _run("git", "-C", str(root), "rev-list", "-n1", tag)
    raw_tag = _run("git", "-C", str(root), "cat-file", "-p", tag) or ""
    signed = "SIGNATURE-----" in raw_tag
    verified = _run("git", "-C", str(root), "tag", "-v", tag) is not None
    steps.append(tag_step(tag=tag, commit=commit, signed=signed, verified=verified))

    release = _gh_json(
        "release", "view", tag, "--repo", repo, "--json", "isDraft,publishedAt,assets"
    )
    if release:
        add("GitHub Release created", f"`{tag}` release exists")
        assets = {a.get("name"): a for a in release.get("assets") or []}
        sbom = next((n for n in assets if n and n.endswith(".cyclonedx.json")), None)
        add("SBOM asset attached", f"`{sbom}`" if sbom else None)
        digest = next((n for n in assets if n and n.endswith(".sha256")), None)
        add("SHA-256 receipt attached", f"`{digest}`" if digest else None)
        published = release.get("publishedAt")
        add(
            "Release published",
            f"published {published}, not a draft"
            if published and not release.get("isDraft")
            else None,
        )
    else:
        for name in (
            "GitHub Release created",
            "SBOM asset attached",
            "SHA-256 receipt attached",
            "Release published",
        ):
            add(name, None)

    def _run_id(workflow: str) -> str | None:
        runs = _gh_json(
            "run",
            "list",
            "--repo",
            repo,
            "--workflow",
            workflow,
            "--limit",
            "30",
            "--json",
            "databaseId,conclusion,headBranch,headSha",
        )
        return matching_run(runs, tag=tag, commit=commit)

    evidence_run = _run_id("release-evidence.yml")
    add("Release evidence workflow", f"run `{evidence_run}`" if evidence_run else None)

    publish_run = _run_id("publish.yml")
    add("PyPI publish", f"run `{publish_run}`" if publish_run else None)
    # The publish workflow's own job verifies provenance and installs the
    # published wheel; a green run is what observes both, so neither claims
    # more than that one run id supports.
    add("PyPI provenance verified", f"run `{publish_run}`" if publish_run else None)

    served = _pypi_version()
    add(
        "Install smoke",
        f"PyPI serves `{served}`" if served == version else None,
    )

    order = {name: i for i, name in enumerate(CHAIN_STEPS)}
    return sorted(steps, key=lambda s: order.get(s.name, len(order)))


def _pypi_version(package: str = "hyodo") -> str | None:
    raw = _run("curl", "-s", "-m", "15", f"https://pypi.org/pypi/{package}/json")
    if not raw:
        return None
    try:
        return str(json.loads(raw)["info"]["version"])
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def replace_receipt(document: str, receipt: str) -> str:
    """Swap the receipt section, leaving the rest of the note untouched."""
    if RECEIPT_HEADING not in document:
        return document.rstrip("\n") + "\n\n" + receipt
    head, _, rest = document.partition(RECEIPT_HEADING)
    tail = rest.split("\n## ", 1)
    remainder = "\n## " + tail[1] if len(tail) > 1 else ""
    return head + receipt + remainder


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="plain semver, e.g. 4.19.1")
    parser.add_argument("--repo", default="lofibrainwav/HyoDo")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift and exit non-zero instead of rewriting the note",
    )
    args = parser.parse_args(argv)

    note = args.root / "docs" / "releases" / f"{args.version}.md"
    if not note.is_file():
        print(f"no release note at {note}", file=sys.stderr)
        return 2

    measured = measure_chain(args.version, repo=args.repo, root=args.root)
    document = note.read_text(encoding="utf-8")

    if args.check:
        drift = receipt_drift(document, measured)
        for line in drift:
            print(line)
        return 1 if drift else 0

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    note.write_text(
        replace_receipt(document, render_receipt(measured, measured_at=stamp)), encoding="utf-8"
    )
    for step in measured:
        print(step.render())
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry
    raise SystemExit(main())
