import asyncio
import importlib.util
import inspect
import json
import time
from pathlib import Path

ROOT = Path(".").resolve()
LOG_DIR = ROOT / "artifacts" / "code_validation_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

GOOD = """
def add(a, b):
    return a + b

print(add(1, 2))
""".lstrip()

BAD_SYNTAX = """
def add(a, b)
    return a + b
""".lstrip()

BAD_RISKY = """
import os
def run(cmd):
    return subprocess.run(cmd, shell=isinstance(cmd, str), check=False).returncode
run("echo hi")
""".lstrip()


def load_module() -> None:
    hits = list(ROOT.rglob("code_review_node.py"))
    if not hits:
        raise SystemExit("code_review_node.py not found")
    target = hits[0]
    spec = importlib.util.spec_from_file_location("ticket045_code_review_node", str(target))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod, target


def parse_result(r) -> None:
    out = {
        "approved": None,
        "score": None,
        "critical_issues_count": None,
        "raw_type": str(type(r)),
    }
    if isinstance(r, dict):
        out["approved"] = r.get("review_approved", r.get("approved"))
        out["score"] = r.get("review_score", r.get("score"))
        crit = r.get("review_critical_issues", r.get("critical_issues"))
        if isinstance(crit, list):
            out["critical_issues_count"] = len(crit)
    return out


async def call_coordinator(mod, code, fname):
    Coordinator = getattr(mod, "CodeReviewCoordinator", None)
    if Coordinator is None:
        return {
            "used": None,
            "notes": ["CodeReviewCoordinator not found"],
            "result": None,
        }

    coord = Coordinator()
    notes = []
    for name in ["review", "run", "execute", "validate", "review_code"]:
        if hasattr(coord, name):
            fn = getattr(coord, name)
            notes.append(f"coordinator.{name} sig={inspect.signature(fn)}")
            try:
                r = fn(code, fname)
            except TypeError:
                r = fn({"review_code": code, "review_file_path": fname})
            if inspect.isawaitable(r):
                r = await r
            return {
                "used": f"CodeReviewCoordinator().{name}",
                "notes": notes,
                "result": r,
            }
    return {
        "used": None,
        "notes": notes + ["Coordinator found but no known method matched"],
        "result": None,
    }


async def call_fallback(mod, code, fname):
    notes = []
    node_obj = getattr(mod, "code_review_node", None)
    if node_obj is not None and hasattr(node_obj, "execute"):
        r = node_obj.execute({"review_code": code, "review_file_path": fname})
        if inspect.isawaitable(r):
            r = await r
        return {"used": "code_review_node.execute", "notes": notes, "result": r}

    exec_fn = getattr(mod, "execute", None)
    if exec_fn is not None:
        r = exec_fn({"review_code": code, "review_file_path": fname})
        if inspect.isawaitable(r):
            r = await r
        return {"used": "module.execute", "notes": notes, "result": r}

    simple = getattr(mod, "simple_syntax_check", None)
    if callable(simple):
        r = simple(code)
        if inspect.isawaitable(r):
            r = await r
        return {"used": "simple_syntax_check (direct)", "notes": notes, "result": r}

    return {"used": None, "notes": ["No callable entrypoint found"], "result": None}


async def run_case(mod, label, code):
    fname = f"{label}.py"
    c = await call_coordinator(mod, code, fname)
    if c["used"] is None:
        f = await call_fallback(mod, code, fname)
        used = f["used"]
        notes = c["notes"] + f["notes"]
        res = f["result"]
        path = "FALLBACK"
    else:
        used = c["used"]
        notes = c["notes"]
        res = c["result"]
        path = "COORDINATOR"

    parsed = parse_result(res)
    return {
        "case": label,
        "path": path,
        "used": used,
        "approved": parsed["approved"],
        "score": parsed["score"],
        "critical_issues_count": parsed["critical_issues_count"],
        "notes": notes,
        "raw_type": parsed["raw_type"],
    }


async def main():
    mod, path = load_module()
    ts = int(time.time())
    out = {
        "ticket": "TICKET-045",
        "as_of": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "code_review_node_path": str(path),
        "cases": [],
        "ssot_phase2_proved": False,
        "criteria": {"must_use_coordinator": True, "must_have_negative_evidence": True},
    }

    good = await run_case(mod, "good", GOOD)
    bad1 = await run_case(mod, "bad_syntax", BAD_SYNTAX)
    bad2 = await run_case(mod, "bad_risky", BAD_RISKY)

    out["cases"] = [good, bad1, bad2]

    used_coord = all(c["path"] == "COORDINATOR" for c in out["cases"])
    neg_ok = any(
        (c["approved"] is False) or ((c["critical_issues_count"] or 0) >= 1)
        for c in out["cases"]
        if c["case"] != "good"
    )

    out["ssot_phase2_proved"] = bool(used_coord and neg_ok)

    out_path = LOG_DIR / f"phase2_multiaagent_proof_{ts}.jsonl"
    out_path.write_text(json.dumps(out, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("WROTE:", out_path)


if __name__ == "__main__":
    asyncio.run(main())
