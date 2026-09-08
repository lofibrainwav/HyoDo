"""Typer surface for local-only HyoDo Friction Contribution v1."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from hyodo.friction import (
    FRICTION_STATE_RELATIVE_PATH,
    NETWORK_TRANSPORT,
    contribution_contract,
    load_friction_state,
    preview_payload,
    save_friction_state,
)

app = typer.Typer(
    name="friction",
    help="Local-only friction contribution preview and consent state",
    add_completion=False,
)
console = Console()


def _root_or_exit(root: str) -> Path:
    path = Path(root).expanduser().resolve()
    if not path.is_dir():
        console.print(f"[red]Workspace root is not a directory: {path}[/red]")
        raise typer.Exit(2)
    return path


@app.command("status")
def friction_status(
    root: str = typer.Option(".", "--root", help="Workspace root that owns .hyodo/"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
) -> None:
    """Show local contribution state. Network transport is disabled in v1."""
    root_path = _root_or_exit(root)
    state = load_friction_state(root_path)
    payload = state.as_dict()
    payload["state_file_present"] = (root_path / FRICTION_STATE_RELATIVE_PATH).is_file()
    payload["nothing_transmitted"] = True
    if json_output:
        console.print_json(json.dumps(payload))
    else:
        color = "green" if state.enabled else "yellow"
        console.print(f"[{color}]{state.state.upper()}[/{color}] Friction Contribution")
        console.print(f"  enabled:           {str(state.enabled).lower()}")
        console.print(f"  consent scope:     {state.consent_scope}")
        console.print("  network consent:   false")
        console.print(f"  network transport: {NETWORK_TRANSPORT}")
        console.print("[dim]No contribution data is transmitted by this release.[/dim]")
    raise typer.Exit(0 if state.state != "unobserved" else 2)


@app.command("preview")
def friction_preview(
    root: str = typer.Option(".", "--root", help="Workspace root that owns the event ledger"),
    run_id: str | None = typer.Option(
        None,
        "--run-id",
        help="Local selection filter only. The run id is never copied into a contribution.",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
) -> None:
    """Preview exactly what could be contributed. This command never sends it."""
    root_path = _root_or_exit(root)
    payload = preview_payload(root_path, run_id=run_id)
    source = payload["observation"]["source"]
    exit_code = 2 if source == "unreadable" else 0
    if json_output:
        payload["exit_code"] = exit_code
        console.print_json(json.dumps(payload))
        raise typer.Exit(exit_code)

    console.print(Panel.fit("HyoDo Friction Contribution Preview", style="bold cyan"))
    console.print(f"network transport: [bold]{NETWORK_TRANSPORT}[/bold]")
    console.print("[bold green]Nothing has been transmitted.[/bold green]")
    console.print(f"runs observed: {payload['observation']['runs_observed']}")
    corrupt = payload["observation"]["corrupt_lines"]
    if corrupt:
        console.print(
            f"[yellow]ledger contains {corrupt} corrupt line(s); source_quality=corrupt[/yellow]"
        )
    contributions = payload["contributions"]
    if not contributions:
        label = "UNOBSERVED" if exit_code == 2 else "No contribution records derived."
        console.print(f"[yellow]{label}[/yellow]")
    for index, contribution in enumerate(contributions, start=1):
        console.print(f"\n[bold]Contribution {index}[/bold]")
        console.print_json(json.dumps(contribution))
    console.print(
        "\n[dim]Raw prompts, responses, code, diffs, paths, secrets, ids, and exact timestamps are never exported by v1.[/dim]"
    )
    console.print(
        "[dim]Population evidence may influence ACL support; it cannot grant authority or override local policy/evidence gates.[/dim]"
    )
    raise typer.Exit(exit_code)


@app.command("on")
def friction_on(
    root: str = typer.Option(".", "--root", help="Workspace root that owns .hyodo/"),
    yes: bool = typer.Option(
        False,
        "--yes",
        help="Explicitly enable local contribution preparation without an interactive prompt",
    ),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
) -> None:
    """Enable local contribution preparation. This is not network consent."""
    root_path = _root_or_exit(root)
    if not yes:
        if not sys.stdin.isatty():
            payload = {
                "ok": False,
                "reason": "confirmation_required: pass --yes",
                "exit_code": 1,
                "network_transport": NETWORK_TRANSPORT,
                "nothing_transmitted": True,
            }
            if json_output:
                console.print_json(json.dumps(payload))
            else:
                console.print(
                    "[yellow]confirmation_required: pass --yes — nothing changed.[/yellow]"
                )
            raise typer.Exit(1)
        if not typer.confirm(
            "Enable local Friction Contribution preparation? No network upload exists in v1."
        ):
            console.print("[yellow]Declined — nothing changed.[/yellow]")
            raise typer.Exit(1)

    state = save_friction_state(root_path, True)
    payload = {"ok": True, **state.as_dict(), "nothing_transmitted": True, "exit_code": 0}
    if json_output:
        console.print_json(json.dumps(payload))
    else:
        console.print("[green]ENABLED[/green] local Friction Contribution preparation")
        console.print("[bold]Network transport remains DISABLED.[/bold]")
        console.print("[dim]A future network collector must ask for fresh, separate consent.[/dim]")
    raise typer.Exit(0)


@app.command("off")
def friction_off(
    root: str = typer.Option(".", "--root", help="Workspace root that owns .hyodo/"),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON"),
) -> None:
    """Disable local contribution preparation immediately."""
    root_path = _root_or_exit(root)
    state = save_friction_state(root_path, False)
    payload = {"ok": True, **state.as_dict(), "nothing_transmitted": True, "exit_code": 0}
    if json_output:
        console.print_json(json.dumps(payload))
    else:
        console.print("[green]DISABLED[/green] Friction Contribution")
        console.print("[dim]Nothing has been transmitted.[/dim]")
    raise typer.Exit(0)


@app.command("contract")
def friction_contract(
    json_output: bool = typer.Option(True, "--json/--no-json", help="Emit the v1 JSON Schema"),
) -> None:
    """Print the strict allow-listed hyodo.friction-contribution/v1 contract."""
    contract = contribution_contract()
    if json_output:
        console.print_json(json.dumps(contract))
    else:
        console.print(json.dumps(contract, indent=2, sort_keys=True), markup=False)
    raise typer.Exit(0)
