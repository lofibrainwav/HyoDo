"""Read-only CLI for emitting receipts from existing dashboard evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer

from hyodo.cli.main import EVIDENCE_SCHEMA_VERSION
from hyodo.lens_evidence import emit_all_lens_evidence

app = typer.Typer(
    name="lens-evidence",
    help="Emit lens evidence receipts from an existing dashboard evidence envelope.",
    add_completion=False,
)


@app.command()
def emit(
    file: Annotated[
        Path, typer.Option(..., "--file", help="Existing dashboard evidence envelope JSON.")
    ],
    subject_sha: Annotated[
        str, typer.Option(..., "--subject-sha", help="Full 40- or 64-character subject SHA.")
    ],
) -> None:
    """Print the six canonical lens-evidence receipts as JSON."""
    try:
        evidence: Any = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        typer.echo(f"Could not read dashboard evidence JSON: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    if (
        not isinstance(evidence, dict)
        or evidence.get("schema_version") != EVIDENCE_SCHEMA_VERSION
        or not isinstance(evidence.get("provenance"), dict)
        or not isinstance(evidence.get("gates"), dict)
    ):
        typer.echo(
            f"Input must be a {EVIDENCE_SCHEMA_VERSION} envelope with provenance and gates objects.",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        receipts = emit_all_lens_evidence(evidence, subject_sha)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(json.dumps(receipts, ensure_ascii=False, indent=2))


__all__ = ["app"]
