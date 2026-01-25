from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Tool:
    id: str
    pillar: str
    evidence_paths: list[str]


def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    for parent in [p, *p.parents]:
        if (parent / "TICKETS.md").exists():
            return parent
    raise SystemExit("Repo root not found (missing TICKETS.md)")


def load_registry(repo_root: Path) -> dict:
    path = repo_root / "packages" / "afo-core" / "AFO" / "tools" / "tool_registry.json"
    if not path.exists():
        sys.exit(f"Registry not found at {path}")
    return json.loads(path.read_text())


def render_skill_py(tool: Tool) -> str:
    # Python code template for the skill
    # We use repr() to handle list serialization of paths properly in f-string context if needed,
    # but here user provided list comprehension logic.
    # We will stick to user's implementation plan logic using json.dumps for path strings.
    import json

    # Construct the candidates list string code
    # evidence_paths are ["p1", "p2"]
    # We want candidates = [repo_root / "p1", repo_root / "p2"]
    # Use json.dumps to quote strings safely.
    paths_code = ", ".join([f"repo_root / {json.dumps(p)}" for p in tool.evidence_paths])

    return f"""from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json

@dataclass(frozen=True)
class ToolSkillResult:
    tool_id: str
    pillar: str
    status: str
    score: int
    evidence: str

def run(repo_root: Path) -> dict:
    # Auto-generated evidence candidates
    candidates = [{paths_code}]

    # Find first existing evidence
    hit = next((p for p in candidates if p.exists()), None)

    if hit and hit.stat().st_size > 0:
        # Resolve relative path for cleaner output if possible
        try:
            rel = str(hit.relative_to(repo_root))
        except ValueError:
            rel = str(hit)

        return asdict(ToolSkillResult("{tool.id}", "{tool.pillar}", "healthy", 90, rel))

    # Fail Loud if no evidence
    return asdict(ToolSkillResult("{tool.id}", "{tool.pillar}", "unhealthy", 10, "missing"))
"""


def main() -> None:
    repo_root = find_repo_root(Path.cwd())
    reg = load_registry(repo_root)
    tools = [Tool(**t) for t in reg["tools"]]

    out_dir = repo_root / "packages" / "afo-core" / "AFO" / "skills" / "tools_generated"

    # Clean recreate
    if out_dir.exists():
        import shutil

        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    (out_dir / "__init__.py").write_text("")

    for t in tools:
        fname = f"{t.id}_skill.py"
        (out_dir / fname).write_text(render_skill_py(t))
        print(f"Generated: {fname}")

    print(f"OK: generated {len(tools)} skills -> {out_dir}")


if __name__ == "__main__":
    main()
