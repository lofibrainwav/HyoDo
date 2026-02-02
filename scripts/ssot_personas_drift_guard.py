import re
import sys
from pathlib import Path

PILLARS = ["truth", "goodness", "beauty", "serenity", "eternity"]


def find_personas_yaml(repo: Path) -> Path:
    candidates = list(repo.rglob("TRINITY_OS_PERSONAS.yaml"))
    if candidates:
        return candidates[0]
    hits = []
    for p in repo.rglob("*.y*ml"):
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "AFO KINGDOM PERSONAS SSOT" in t and "source_of_truth" in t:
            hits.append(p)
    if hits:
        return hits[0]
    raise FileNotFoundError("SSOT personas yaml not found")


def extract_yaml_weights(text: str) -> dict:
    out = {}
    # Principles block usually contains the definitive weights
    for k in PILLARS:
        # Match 'pillar:' followed by indentation and 'weight:'
        # This specifically targets the nested structure in principles.pillars
        pattern = rf"\s+{k}:\s*\n\s+(?:.*?\n)*?\s+weight:\s*([0-9.]+)"
        m = re.search(pattern, text)
        if not m:
            # Fallback: simple match but avoid 'total_weight'
            # Use negative lookbehind or just match beginning of line/spaces
            pattern = rf"(?<!total_){k}:\s*([0-9.]+)"
            m = re.search(pattern, text)
        if not m:
            # Match strategist block: 'pillar: "name"' then 'weight: X'
            pattern = rf"pillar:\s*\"{k}\"\s*\n\s*weight:\s*([0-9.]+)"
            m = re.search(pattern, text)

        if not m:
            raise ValueError(f"missing weight for pillar: {k}")
        out[k] = float(m.group(1))
    return out


def find_code_weight_sources(repo: Path) -> list[Path]:
    patterns = ["trinity", "ssot", "weights", "Friction Calculator v2.0"]
    files = []
    for p in repo.rglob("*.py"):
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if any(s.lower() in t.lower() for s in patterns):
            if any(k in t for k in ("beauty", "serenity", "eternity", "TRINITY", "WEIGHT")):
                files.append(p)
    return files[:30]


def extract_code_weights(text: str) -> dict:
    out = {}
    for k in PILLARS:
        # Match 'pillar': 0.XX (decimal weights) or weight=0.XX
        # This avoiding 100.0 which are scores
        pattern = rf'["\']{k}["\']\s*:\s*(0\.[0-9]+)'
        m = re.search(pattern, text)
        if not m:
            pattern = rf"{k}_weight\s*[:=]\s*(0\.[0-9]+)"
            m = re.search(pattern, text)
        if not m:
            # Also allow explicit TRINITY_WEIGHTS = { "truth": 0.35 } structure
            pattern = rf'["\']{k}["\']\s*:\s*([0|1]\.[0-9]+)'
            m = re.search(pattern, text)

        if m:
            out[k] = float(m.group(1))
    return out


def main() -> int:
    repo = Path.cwd()
    ssot_path = find_personas_yaml(repo)
    ssot_text = ssot_path.read_text(encoding="utf-8", errors="ignore")
    ssot_weights = extract_yaml_weights(ssot_text)

    code_files = find_code_weight_sources(repo)
    best = None
    best_path = None
    for p in code_files:
        t = p.read_text(encoding="utf-8", errors="ignore")
        cw = extract_code_weights(t)
        if len(cw) >= 3:
            best = cw
            best_path = p
            if all(k in cw for k in PILLARS):
                break

    print(f"SSOT: {ssot_path}")
    print(f"SSOT_WEIGHTS: {ssot_weights}")

    if not best:
        print("CODE_WEIGHTS: not detected (no matching dict literals found)")
        return 0

    print(f"CODE_FILE: {best_path}")
    print(f"CODE_WEIGHTS: {best}")

    drift = {}
    for k in PILLARS:
        if k in best and abs(best[k] - ssot_weights[k]) > 1e-9:
            drift[k] = (ssot_weights[k], best[k])
        if k not in best:
            drift[k] = (ssot_weights[k], None)

    if drift:
        print("DRIFT: YES")
        for k, (s, c) in drift.items():
            print(f"- {k}: ssot={s} code={c}")
        return 2

    print("DRIFT: NO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
