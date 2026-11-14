"""Regression tests for the fourth verification round of PR #621 (at b25e809).

Seeded from `test_v621_round2.py`: stale-lock recovery must not race a new
run, a restore must never write through a planted hard link, the execution
snapshot is reported as provided rather than as what ran, recovery waits for
the killed run's skill process groups, and a timeout reports its group kill.
"""

from __future__ import annotations

import contextlib
import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from test_factory_adversarial_review import _auto_run, _forge, _module
from test_factory_harness import (
    FACTORY_PATH,
    _host_authority,
    _init_clean_repo,
    _load_factory_module,
    _write_skill,
)

ROOT = Path(__file__).resolve().parents[1]


def _lifecycle() -> Any:
    return sys.modules["factory.lifecycle"]


def _dead_pid() -> int:
    proc = subprocess.Popen(["true"])
    proc.wait()
    return proc.pid


def _scoped(tmp_path: Path) -> tuple[Any, Path]:
    factory = _load_factory_module()
    repo = tmp_path / "ws"
    _init_clean_repo(repo)
    pkg = tmp_path / "scoped"
    sd = _write_skill(
        pkg, "tdd-one", "---\ncategory: engineering\nsubprocess_exec: true\n---\n# T\nTDD.\n"
    )
    (sd / "run.sh").write_text("echo x\n", encoding="utf-8")
    _write_skill(pkg, "office-doc", "---\ncategory: office\n---\n# Office\nDocs.\n")
    factory.add_module(repo, pkg, module_id="scoped")
    return factory, repo


def _flags(factory: Any, repo: Path) -> dict[str, bool]:
    return {
        sid: u.enabled
        for m in factory.load_registry_state(repo).values()
        for sid, u in m.skills.items()
    }


def _pgrep(tag: str) -> list[str]:
    return subprocess.run(["pgrep", "-f", tag], capture_output=True, text=True).stdout.split()


def _kill_groups_of(tag: str) -> None:
    """Kill the whole process group of every process whose command line has *tag*."""
    for pid in _pgrep(tag):
        with contextlib.suppress(ProcessLookupError, PermissionError, ValueError):
            os.killpg(os.getpgid(int(pid)), signal.SIGKILL)


# 1. Recovery and a new run cannot interleave --------------------------------


def test_recovery_restores_the_killed_run_before_a_new_run_can_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factory, repo = _scoped(tmp_path)
    lifecycle = _lifecycle()
    before = _flags(factory, repo)
    # A killed selective run: stranded flags, its pending record, a stale lock.
    lifecycle.save_pending_selective_restore(
        repo, "killed", lifecycle.snapshot_activation_state(repo)
    )
    modules = factory.load_registry_state(repo)
    mod = modules["scoped"]
    modules["scoped"] = replace(
        mod,
        skills={
            sid: replace(u, enabled=(sid == "scoped/tdd-one")) for sid, u in mod.skills.items()
        },
    )
    lifecycle.save_registry_state(repo, modules)
    lock_path = repo / ".hyodo" / "factory" / "run.lock"
    lock_path.write_text(
        json.dumps({"run_id": "killed", "pid": _dead_pid(), "host": socket.gethostname()}),
        encoding="utf-8",
    )

    newcomer: dict[str, Any] = {}

    def newcomer_run() -> None:
        try:
            lifecycle.acquire_run_lock(repo, "newcomer")
            newcomer["acquired_at"] = time.monotonic()
        except RuntimeError as exc:
            newcomer["error"] = str(exc)

    real_save = lifecycle.save_registry_state
    window: dict[str, float] = {}

    def save_while_a_run_tries_to_start(root: Path, mods: Any) -> None:
        thread = threading.Thread(target=newcomer_run)
        thread.start()
        newcomer["thread"] = thread
        time.sleep(0.4)  # give the newcomer every chance to slip in
        window["restore_end"] = time.monotonic()
        real_save(root, mods)

    monkeypatch.setattr(lifecycle, "save_registry_state", save_while_a_run_tries_to_start)
    receipt = lifecycle.recover_stale_run_lock(repo)
    monkeypatch.setattr(lifecycle, "save_registry_state", real_save)
    newcomer["thread"].join(timeout=10)

    # The newcomer only got the lock after recovery had finished restoring.
    assert newcomer.get("acquired_at", 0) > window["restore_end"]
    assert _flags(factory, repo) == before
    assert "scoped/office-doc" in receipt["selective_flags_restored"]
    assert receipt["run_id"] == "killed"
    held = json.loads(lock_path.read_text(encoding="utf-8"))
    assert held["run_id"] == "newcomer"
    lifecycle.release_run_lock(repo)


def test_pending_selective_records_are_keyed_by_run_id(tmp_path: Path) -> None:
    _factory, repo = _scoped(tmp_path)
    lifecycle = _lifecycle()
    snap = lifecycle.snapshot_activation_state(repo)
    lifecycle.save_pending_selective_restore(repo, "run-a", snap)
    lifecycle.save_pending_selective_restore(repo, "run-b", snap)
    lifecycle.clear_pending_selective_restore(repo, "run-a")
    assert lifecycle.load_pending_selective_restore(repo, "run-a") is None
    assert lifecycle.load_pending_selective_restore(repo, "run-b") == snap
    assert lifecycle.pending_selective_runs(repo) == ["run-b"]


# 2. A restore never writes through a planted hard link ----------------------


def test_restore_never_writes_or_chmods_through_a_planted_hard_link(tmp_path: Path) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "ws"
    _init_clean_repo(repo)
    mod, _ = _module(tmp_path, "ro", script="echo x\n", frontmatter="filesystem_write: false\n")
    factory.add_module(repo, mod, module_id="ro")
    outside = tmp_path / "outside_secret.txt"
    outside.write_text("OUTSIDE ORIGINAL\n", encoding="utf-8")
    outside.chmod(0o600)
    outside_key = tmp_path / "outside_key"
    outside_key.write_text("KEY\n", encoding="utf-8")
    outside_key.chmod(0o400)
    original_app = (repo / "app.py").read_text(encoding="utf-8")
    cmd = [
        "sh",
        "-c",
        f'chmod u+w . && rm -f app.py && ln "{outside}" app.py && ln "{outside_key}" newlink && echo planted',
    ]
    res = factory.execute_modular_run(
        repo, run_id="r-hl", prompt="implement tdd", skill_commands={"ro/tdd": cmd}
    )
    assert outside.read_text(encoding="utf-8") == "OUTSIDE ORIGINAL\n"
    assert outside.stat().st_mode & 0o777 == 0o600
    assert outside_key.stat().st_mode & 0o777 == 0o400
    assert (repo / "app.py").read_text(encoding="utf-8") == original_app
    assert (repo / "app.py").stat().st_nlink == 1
    assert not (repo / "newlink").exists()
    violations = " ".join(res["permission_violations"])
    assert "hardlink_planted:app.py" in violations
    assert "hardlink_planted:newlink" in violations


# 3. The execution snapshot is provided, not proven to be what ran -------------


def test_split_original_path_is_not_reported_as_running_from_the_snapshot(tmp_path: Path) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "ws"
    _init_clean_repo(repo)
    vmod, _ = _module(tmp_path, "zvictim", script="echo VICTIM_APPROVED_V1\n")
    factory.add_module(repo, vmod, module_id="zvictim")
    original = str(vmod.resolve())
    head, tail = original[:-3], original[-3:] + "/skills/tdd"
    cmd = ["sh", "-c", f'sh "{head}""{tail}/run.sh"']
    _forge(factory, repo, "zvictim/tdd", command=cmd, run_id="ok")
    out = _auto_run(factory, repo, "r-split", {"zvictim/tdd": cmd}, _host_authority({"ok"}))[
        "skill_outputs"
    ]["zvictim/tdd"]
    assert out["execution_state"] == "EXECUTED_PASS"
    assert out["executed_from"] != "MODULE_SNAPSHOT"
    assert out["executed_from"] == "MODULE_SNAPSHOT_PROVIDED"
    assert out["module_snapshot_coverage"] == "UNOBSERVED"


# 4. Recovery waits for the killed run's skill process groups -----------------


def test_recovery_refuses_while_a_killed_runs_skill_group_is_alive(tmp_path: Path) -> None:
    factory, repo = _scoped(tmp_path)
    marker = tmp_path / "started.marker"
    tag = f"r4orphan{os.getpid()}"
    script = (
        "import importlib.util, pathlib\n"
        f"spec = importlib.util.spec_from_file_location('hf', {str(FACTORY_PATH)!r})\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        f"m.execute_modular_run(pathlib.Path({str(repo)!r}), run_id='victim', prompt='implement tdd',"
        f" timeout_s=60, skill_commands={{'scoped/tdd-one': ['sh', '-c', 'touch {marker}; sleep 30 # {tag}']}})\n"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", script], env={**os.environ, "PYTHONPATH": str(ROOT)}
    )
    try:
        for _ in range(300):
            if marker.exists():
                break
            time.sleep(0.1)
        assert marker.exists(), "the run never started its skill"
        os.kill(proc.pid, signal.SIGKILL)
        proc.wait()
        assert _pgrep(tag), "the skill should outlive its killed owner"
        with pytest.raises(RuntimeError, match="NOT_PROVABLY_STALE"):
            factory.recover_stale_run_lock(repo)
        assert (repo / ".hyodo" / "factory" / "run.lock").exists()
    finally:
        _kill_groups_of(tag)
        with contextlib.suppress(ProcessLookupError):
            proc.kill()
    groups = _lifecycle().recorded_process_groups(repo, "victim") or []
    for _ in range(100):
        if not any(_lifecycle()._process_group_alive(g) for g in groups):
            break
        time.sleep(0.05)
    receipt = factory.recover_stale_run_lock(repo)
    assert receipt["run_id"] == "victim"
    assert not (repo / ".hyodo" / "factory" / "run.lock").exists()


# 5. A timeout reports the group kill ------------------------------------------


def test_timeout_reports_that_the_process_group_was_killed(tmp_path: Path) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "ws"
    _init_clean_repo(repo)
    mod, _ = _module(tmp_path, "slow", script="echo x\n", frontmatter="filesystem_write: false\n")
    factory.add_module(repo, mod, module_id="slow")
    tag = f"r4timeout{os.getpid()}"
    cmd = ["sh", "-c", f"sleep 30 # {tag}-bg & sleep 30 # {tag}-fg"]
    try:
        res = factory.execute_modular_run(
            repo,
            run_id="r-to",
            prompt="implement tdd",
            timeout_s=1.0,
            skill_commands={"slow/tdd": cmd},
        )
        time.sleep(0.3)
        left = _pgrep(tag)
    finally:
        subprocess.run(["pkill", "-f", tag], check=False)
    out = res["skill_outputs"]["slow/tdd"]
    assert out["execution_state"] == "TIMEOUT"
    assert out["descendants_killed_after_exit"] is True
    assert out["process_group_killed_on_timeout"] is True
    assert left == []


def test_zombie_pid_and_process_group_count_as_gone_not_alive(tmp_path: Path) -> None:
    factory, repo = _scoped(tmp_path)
    lifecycle = _lifecycle()
    # A child that exited cleanly but has not yet been reaped stays <defunct> (`Z`).
    zombie = subprocess.Popen(["true"], start_new_session=True)
    try:
        # Wait until the child finishes executing and becomes a zombie (without calling wait()).
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and lifecycle._pid_alive(zombie.pid):
            time.sleep(0.02)
        assert lifecycle._pid_alive(zombie.pid) is False
        assert lifecycle._process_group_state(zombie.pid) == "GONE"

        lock = repo / ".hyodo" / "factory" / "run.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(
            json.dumps(
                {
                    "run_id": "zombie-run",
                    "pid": zombie.pid,
                    "host": socket.gethostname(),
                }
            ),
            encoding="utf-8",
        )
        lifecycle.write_skill_process_groups(repo, "zombie-run", [zombie.pid])
        receipt = factory.recover_stale_run_lock(repo)
        assert receipt["owner_state"] == "STALE"
        assert not lock.exists()
    finally:
        zombie.wait()


def test_proc_read_or_parse_failure_with_zombie_fails_closed_as_alive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lifecycle = _lifecycle()
    zombie = subprocess.Popen(["true"], start_new_session=True)
    try:
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and lifecycle._pid_alive(zombie.pid):
            time.sleep(0.02)
        assert lifecycle._pid_alive(zombie.pid) is False

        orig_read_text = Path.read_text

        def read_with_unreadable_peer(self: Path, *args: Any, **kwargs: Any) -> str:
            if (
                self.parent.parent == Path("/proc")
                and self.name == "stat"
                and self.parent.name != str(zombie.pid)
                and self.parent.name.isdigit()
            ):
                raise PermissionError("simulated /proc read failure")
            return orig_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", read_with_unreadable_peer)
        assert lifecycle._process_group_state(zombie.pid) == "ALIVE"

        def read_with_corrupt_peer(self: Path, *args: Any, **kwargs: Any) -> str:
            if (
                self.parent.parent == Path("/proc")
                and self.name == "stat"
                and self.parent.name != str(zombie.pid)
                and self.parent.name.isdigit()
            ):
                return "123 (corrupt-line"
            return orig_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", read_with_corrupt_peer)
        assert lifecycle._process_group_state(zombie.pid) == "ALIVE"
    finally:
        zombie.wait()


def test_ps_fallback_timeout_expired_and_mixed_output_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lifecycle = _lifecycle()
    orig_is_file = Path.is_file

    def no_proc_self_stat(self: Path) -> bool:
        if self == Path("/proc/self/stat"):
            return False
        return orig_is_file(self)

    monkeypatch.setattr(Path, "is_file", no_proc_self_stat)
    monkeypatch.setattr(os, "kill", lambda pid, sig: None)
    monkeypatch.setattr(os, "killpg", lambda pgid, sig: None)

    def raise_timeout(*args: Any, **kwargs: Any) -> Any:
        raise subprocess.TimeoutExpired(cmd=["ps"], timeout=2.0)

    monkeypatch.setattr(subprocess, "run", raise_timeout)
    assert lifecycle._pid_alive(99999) is True
    assert lifecycle._process_group_state(99999) == "ALIVE"

    def ps_mixed_and_malformed(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["ps"],
            returncode=0,
            stdout="99999 Z\nmalformed-line\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", ps_mixed_and_malformed)
    assert lifecycle._process_group_state(99999) == "ALIVE"

    def ps_live_plus_zombie(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["ps"],
            returncode=0,
            stdout="99999 Z\n99999 S\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", ps_live_plus_zombie)
    assert lifecycle._process_group_state(99999) == "ALIVE"


def test_mixed_live_and_zombie_in_same_process_group_refuses_recovery(tmp_path: Path) -> None:
    factory, repo = _scoped(tmp_path)
    lifecycle = _lifecycle()
    marker = tmp_path / "live_started"
    # Spawn a child group holding one unwaited exited zombie (`true`) and one live `sleep`.
    code = (
        "import os, pathlib, subprocess, time\n"
        f"pathlib.Path({str(marker)!r}).write_text(str(os.getpgrp()), encoding='utf-8')\n"
        "z = subprocess.Popen(['true'])\n"
        "try:\n"
        "    time.sleep(30)\n"
        "finally:\n"
        "    z.wait()\n"
    )
    holder = subprocess.Popen([sys.executable, "-c", code], start_new_session=True)
    try:
        for _ in range(100):
            if marker.exists():
                break
            time.sleep(0.05)
        assert marker.exists()
        time.sleep(0.2)  # let `true` become an exited zombie while `holder` stays alive
        assert lifecycle._process_group_state(holder.pid) == "ALIVE"

        dead = subprocess.Popen(["true"])
        dead.wait()
        lock = repo / ".hyodo" / "factory" / "run.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(
            json.dumps({"run_id": "mixed-run", "pid": dead.pid, "host": socket.gethostname()}),
            encoding="utf-8",
        )
        lifecycle.write_skill_process_groups(repo, "mixed-run", [holder.pid])
        with pytest.raises(RuntimeError, match="RUN_LOCK_NOT_PROVABLY_STALE:ORPHANED_SKILLS"):
            factory.recover_stale_run_lock(repo)
        assert lock.exists()
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(holder.pid, signal.SIGKILL)
        holder.wait()


def test_sigkill_before_pgid_registration_prevents_skill_execution(tmp_path: Path) -> None:
    factory, repo = _scoped(tmp_path)
    before_persist = tmp_path / "before_persist.marker"
    skill_marker = tmp_path / "skill_should_not_run.marker"
    tag = f"r4prereg{os.getpid()}"
    script = (
        "import importlib.util, pathlib, signal, sys\n"
        f"spec = importlib.util.spec_from_file_location('hf', {str(FACTORY_PATH)!r})\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "runner = sys.modules['factory.runner']\n"
        "def pause_before_write(ws, rid, pgids):\n"
        f"    pathlib.Path({str(before_persist)!r}).write_text(','.join(map(str, pgids)), encoding='utf-8')\n"
        "    while True:\n"
        "        signal.pause()\n"
        "runner.write_skill_process_groups = pause_before_write\n"
        f"m.execute_modular_run(pathlib.Path({str(repo)!r}), run_id='sigkill-pre-reg', prompt='implement tdd',"
        f" timeout_s=60, skill_commands={{'scoped/tdd-one': ['sh', '-c', 'touch {skill_marker}; sleep 30 # {tag}']}})\n"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", script], env={**os.environ, "PYTHONPATH": str(ROOT)}
    )
    try:
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline and not before_persist.exists():
            time.sleep(0.01)
        assert before_persist.exists(), "parent never reached PGID registration"
        os.kill(proc.pid, signal.SIGKILL)
        proc.wait()
        # Wait for the gated child trampoline to observe EOF and exit (reaped or zombie).
        recorded_pgid = int(before_persist.read_text(encoding="utf-8"))
        child_deadline = time.monotonic() + 5.0
        while time.monotonic() < child_deadline and _lifecycle()._pid_alive(recorded_pgid):
            time.sleep(0.01)
        assert not skill_marker.exists(), "skill executed before PGID was persisted"
        assert _pgrep(tag) == []
    finally:
        _kill_groups_of(tag)
        with contextlib.suppress(ProcessLookupError):
            proc.kill()
    receipt = factory.recover_stale_run_lock(repo)
    assert receipt["run_id"] == "sigkill-pre-reg"
    assert not (repo / ".hyodo" / "factory" / "run.lock").exists()


def test_sigkill_after_pgid_persist_before_gate_byte_recovers_cleanly(tmp_path: Path) -> None:
    factory, repo = _scoped(tmp_path)
    persisted = tmp_path / "persisted.marker"
    skill_marker = tmp_path / "skill_should_not_run.marker"
    tag = f"r4midgate{os.getpid()}"
    script = (
        "import importlib.util, pathlib, signal, sys\n"
        f"spec = importlib.util.spec_from_file_location('hf', {str(FACTORY_PATH)!r})\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "runner = sys.modules['factory.runner']\n"
        "real_write = runner.write_skill_process_groups\n"
        "def pause_after_write(ws, rid, pgids):\n"
        "    data = real_write(ws, rid, pgids)\n"
        f"    pathlib.Path({str(persisted)!r}).write_text(','.join(map(str, pgids)), encoding='utf-8')\n"
        "    while True:\n"
        "        signal.pause()\n"
        "runner.write_skill_process_groups = pause_after_write\n"
        f"m.execute_modular_run(pathlib.Path({str(repo)!r}), run_id='sigkill-mid-gate', prompt='implement tdd',"
        f" timeout_s=60, skill_commands={{'scoped/tdd-one': ['sh', '-c', 'touch {skill_marker}; sleep 30 # {tag}']}})\n"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", script], env={**os.environ, "PYTHONPATH": str(ROOT)}
    )
    try:
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline and not persisted.exists():
            time.sleep(0.01)
        assert persisted.exists(), "parent never persisted PGID"
        os.kill(proc.pid, signal.SIGKILL)
        proc.wait()
        groups = _lifecycle().recorded_process_groups(repo, "sigkill-mid-gate")
        assert groups is not None
        assert len(groups) == 1
        child_deadline = time.monotonic() + 5.0
        while time.monotonic() < child_deadline and any(
            _lifecycle()._process_group_alive(g) for g in groups
        ):
            time.sleep(0.01)
        assert not skill_marker.exists(), "skill executed before gate byte was sent"
        assert _pgrep(tag) == []
    finally:
        _kill_groups_of(tag)
        with contextlib.suppress(ProcessLookupError):
            proc.kill()
    receipt = factory.recover_stale_run_lock(repo)
    assert receipt["run_id"] == "sigkill-mid-gate"
    assert not (repo / ".hyodo" / "factory" / "run.lock").exists()


def test_registration_failure_prevents_exec_and_reaps_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factory, repo = _scoped(tmp_path)
    runner = sys.modules["factory.runner"]
    skill_marker = tmp_path / "exec_after_fail.marker"
    tag = f"r4regfail{os.getpid()}"
    seen_pids: list[int] = []

    def fail_on_start(pgid: int) -> None:
        seen_pids.append(pgid)
        raise OSError("simulated disk full during PGID registration")

    with pytest.raises(OSError, match="simulated disk full"):
        runner._run_skill_process(
            ["sh", "-c", f"touch {skill_marker}; sleep 30 # {tag}"],
            cwd=repo,
            env=dict(os.environ),
            timeout=5.0,
            on_start=fail_on_start,
        )
    assert len(seen_pids) == 1
    assert not skill_marker.exists()
    assert _pgrep(tag) == []
    # Reaping guarantees the child PID is completely gone (not even a zombie).
    with pytest.raises(ProcessLookupError):
        os.kill(seen_pids[0], 0)

    def fail_write(*_args: Any, **_kwargs: Any) -> bytes:
        raise OSError("simulated disk full")

    monkeypatch.setattr(runner, "write_skill_process_groups", fail_write)
    res = factory.execute_modular_run(
        repo,
        run_id="reg-fail-run",
        prompt="implement tdd",
        skill_commands={"scoped/tdd-one": ["sh", "-c", f"touch {skill_marker}; sleep 30 # {tag}"]},
    )
    assert res["skill_outputs"]["scoped/tdd-one"]["execution_state"] == "EXECUTED_FAIL"
    assert not skill_marker.exists()
    assert _pgrep(tag) == []
    assert not (repo / ".hyodo" / "factory" / "run.lock").exists()


def test_parallel_wave_registers_all_pgids_before_skills_execute(tmp_path: Path) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "ws"
    _init_clean_repo(repo)
    pkg = tmp_path / "par"
    for name in ("tdd-one", "tdd-two"):
        _write_skill(
            pkg,
            name,
            (
                f"---\nname: {name}\ncategory: engineering\n"
                "subprocess_exec: true\nfilesystem_write: false\n---\n"
                f"# {name}\nTDD engineering skill.\n"
            ),
        )
    factory.add_module(repo, pkg, module_id="par")
    probe = (
        "import glob, json, os, sys\n"
        "files = glob.glob('.hyodo/factory-run-state/*.process_groups.json')\n"
        "assert files, 'missing process_groups.json at skill exec time'\n"
        "pgid = os.getpgrp()\n"
        "data = json.load(open(files[0], encoding='utf-8'))\n"
        "assert pgid in data['pgids'], f'{pgid} not in {data}'\n"
        "print(f'OK:{pgid}')\n"
    )
    res = factory.execute_modular_run(
        repo,
        run_id="par-wave",
        prompt="implement tdd",
        deduplicate_by_slot=False,
        skill_commands={
            "par/tdd-one": [sys.executable, "-c", probe],
            "par/tdd-two": [sys.executable, "-c", probe],
        },
    )
    assert res["execution_summary"]["parallel_waves_executed"] == 1
    for sid in ("par/tdd-one", "par/tdd-two"):
        out = res["skill_outputs"][sid]
        assert out["execution_state"] == "EXECUTED_PASS"
        assert out["stdout"].startswith("OK:")

    # Registration failure in a parallel wave also prevents execution and reaps children.
    runner = sys.modules["factory.runner"]
    real_write = runner.write_skill_process_groups
    skill_marker = tmp_path / "par_fail.marker"
    tag = f"r4parfail{os.getpid()}"

    def fail_on_second(ws: Path, rid: str, pgids: list[int]) -> bytes:
        if len(pgids) >= 2:
            raise OSError("parallel registration write failure")
        return real_write(ws, rid, pgids)

    orig_write = runner.write_skill_process_groups
    runner.write_skill_process_groups = fail_on_second
    try:
        par_fail = factory.execute_modular_run(
            repo,
            run_id="par-wave-fail",
            prompt="implement tdd",
            deduplicate_by_slot=False,
            timeout_s=1.0,
            skill_commands={
                "par/tdd-one": ["sh", "-c", f"touch {skill_marker}; sleep 30 # {tag}"],
                "par/tdd-two": ["sh", "-c", f"touch {skill_marker}; sleep 30 # {tag}"],
            },
        )
    finally:
        runner.write_skill_process_groups = orig_write
        _kill_groups_of(tag)
    assert par_fail["execution_summary"]["parallel_waves_executed"] == 1
    states = {
        par_fail["skill_outputs"][s]["execution_state"] for s in ("par/tdd-one", "par/tdd-two")
    }
    assert "EXECUTED_FAIL" in states
    assert _pgrep(tag) == []
    assert not (repo / ".hyodo" / "factory" / "run.lock").exists()


def test_incomplete_lock_and_malformed_process_group_records_fail_closed(tmp_path: Path) -> None:
    factory, repo = _scoped(tmp_path)
    lifecycle = _lifecycle()

    # 1. Empty run.lock (killed between O_CREAT|O_EXCL and os.write)
    lock = repo / ".hyodo" / "factory" / "run.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("", encoding="utf-8")
    status = lifecycle.run_lock_status(repo)
    assert status is not None
    assert status["state"] == "UNKNOWN"
    assert status["unknown_reason"] == "lock_unreadable"
    with pytest.raises(RuntimeError, match="RUN_LOCK_NOT_PROVABLY_STALE:UNKNOWN"):
        factory.recover_stale_run_lock(repo)

    # 2. Dead owner + broken symlink / wrong-type pgids in process_groups.json
    dead = subprocess.Popen(["true"])
    dead.wait()
    lock.write_text(
        json.dumps({"run_id": "bad-rec", "pid": dead.pid, "host": socket.gethostname()}),
        encoding="utf-8",
    )
    rec_path = repo / lifecycle.process_groups_record_rel("bad-rec")
    rec_path.parent.mkdir(parents=True, exist_ok=True)
    rec_path.symlink_to(tmp_path / "does_not_exist")
    assert lifecycle.recorded_process_groups(repo, "bad-rec") is None
    status = lifecycle.run_lock_status(repo)
    assert status is not None
    assert status["state"] == "UNKNOWN"
    assert status["unknown_reason"] == "process_group_record_invalid"
    with pytest.raises(RuntimeError, match="process_group_record_invalid"):
        factory.recover_stale_run_lock(repo)
    rec_path.unlink()

    for bad_payload in (
        json.dumps({"run_id": "bad-rec", "pgids": "123"}),
        json.dumps({"run_id": "bad-rec", "pgids": [True]}),
        json.dumps({"run_id": "bad-rec", "pgids": {"1": 2}}),
    ):
        rec_path.write_text(bad_payload, encoding="utf-8")
        assert lifecycle.recorded_process_groups(repo, "bad-rec") is None
        with pytest.raises(RuntimeError, match="process_group_record_invalid"):
            factory.recover_stale_run_lock(repo)


def test_pid_reuse_fails_closed_as_live(tmp_path: Path) -> None:
    factory, repo = _scoped(tmp_path)
    lifecycle = _lifecycle()
    reused = subprocess.Popen(["sleep", "30"], start_new_session=True)
    try:
        lock = repo / ".hyodo" / "factory" / "run.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text(
            json.dumps({"run_id": "reused", "pid": reused.pid, "host": socket.gethostname()}),
            encoding="utf-8",
        )
        status = lifecycle.run_lock_status(repo)
        assert status is not None
        assert status["state"] == "LIVE"
        with pytest.raises(RuntimeError, match="RUN_LOCK_NOT_PROVABLY_STALE:LIVE"):
            factory.recover_stale_run_lock(repo)
        assert lock.exists()
    finally:
        reused.kill()
        reused.wait()
