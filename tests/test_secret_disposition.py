from __future__ import annotations

from pathlib import Path

from scripts.check_secret_disposition import check


def row(finding_id: int, disposition: str, reason: str = "synthetic fixture") -> str:
    return f"| {finding_id} | rule | path | commit | 1 | {reason} | `{disposition}` |"


def register(tmp_path: Path, dispositions: dict[int, str]) -> Path:
    path = tmp_path / "register.md"
    path.write_text("\n".join(row(i, dispositions[i]) for i in dispositions) + "\n")
    return path


def test_all_closed_with_reasons_passes(tmp_path: Path) -> None:
    path = register(tmp_path, dict.fromkeys(range(1, 17), "SYNTHETIC"))
    assert check(path, 16) == []


def test_pending_owner_fails_closed(tmp_path: Path) -> None:
    dispositions = dict.fromkeys(range(1, 17), "SYNTHETIC")
    dispositions[10] = "PENDING_OWNER"
    path = register(tmp_path, dispositions)
    assert check(path, 16) == ["finding 10: PENDING_OWNER"]


def test_missing_and_duplicate_ids_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "register.md"
    path.write_text("\n".join([row(1, "SYNTHETIC"), row(1, "SYNTHETIC")]))
    errors = check(path, 2)
    assert "register unreadable or invalid: duplicate finding id: 1" in errors
