from __future__ import annotations

import json
import subprocess
from pathlib import Path

from test_release_prepare import write_minimal_repo

from scripts.release.plan_release import plan_release
from scripts.release.prepare_release import prepare_release
from scripts.release.release_state import start_receipt, transition, validate_receipt


def init_checkout(root: Path, branch: str) -> None:
    subprocess.run(
        ["git", "-C", str(root), "init", "-b", branch],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True, capture_output=True, text=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=HyoDo test",
            "-c",
            "user.email=test@hyodo.invalid",
            "commit",
            "-m",
            "baseline",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "branch", "-f", "origin/main", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )


def test_plan_is_zero_write_and_passes_on_release_branch(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)
    init_checkout(tmp_path, "release/4.12.0")
    before = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    receipt = plan_release(tmp_path, "4.12.0", base_ref="origin/main")

    after = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert receipt["result"] == "PASS"
    assert receipt["zero_write"] is True
    assert receipt["expected_version_delta"] == {"from": "4.11.0", "to": "4.12.0"}
    assert before == after


def test_plan_blocks_main_and_reports_json_shape(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)
    init_checkout(tmp_path, "main")

    receipt = plan_release(tmp_path, "4.12.0", base_ref="origin/main")

    assert receipt["result"] == "BLOCK"
    assert any(
        item["name"] == "named_release_branch" and item["state"] == "BLOCK"
        for item in receipt["validations"]
    )
    json.dumps(receipt)


def test_passing_plan_enters_planned_state_and_transitions_fail_closed(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)
    init_checkout(tmp_path, "release/4.12.0")

    plan = plan_release(tmp_path, "4.12.0", base_ref="origin/main")
    receipt = start_receipt(plan)
    validate_receipt(receipt)
    verified = transition(receipt, "AUTHORIZED", "explicit authority ref=approval-1")

    assert receipt["state"] == "PLANNED"
    assert verified["state"] == "AUTHORIZED"
    validate_receipt(verified)


def test_plan_passes_for_fully_prepared_candidate(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)
    init_checkout(tmp_path, "release/4.12.0")
    prepare_release(tmp_path, "4.12.0", today="2026-09-23")
    roadmap = tmp_path / "ROADMAP.md"
    roadmap.write_text(
        roadmap.read_text() + "\n### 4.12.0\n\n- Prepared candidate.\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=HyoDo test",
            "-c",
            "user.email=test@hyodo.invalid",
            "commit",
            "-m",
            "prepare candidate",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    plan = plan_release(tmp_path, "4.12.0", base_ref="origin/main")

    assert plan["result"] == "PASS"
    assert plan["candidate_state"] == "PREPARED"
    assert plan["expected_version_delta"] == {"from": "4.11.0", "to": "4.12.0"}
