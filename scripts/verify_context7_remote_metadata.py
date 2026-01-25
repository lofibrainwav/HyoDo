import json
import os
import re
from urllib.request import Request, urlopen

BASE = os.environ.get("AFO_BASE_URL", "http://127.0.0.1:8010").rstrip("/")
META_PATH = os.environ.get("CONTEXT7_META_JSON", "docs/context7_integration_metadata.json")


def http_json(url: str) -> object:
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def norm_path(p: str) -> str:
    p = p.strip().replace("\\", "/")
    p = re.sub(r"^\./+", "", p)
    p = re.sub(r"^/app/", "", p)  # container absolute -> repo relative
    return p


def as_list(x) -> list[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [str(v).strip() for v in x if str(v).strip()]
    if isinstance(x, str):
        return [s.strip() for s in re.split(r"[,\n]+", x) if s.strip()]
    return []


def extract_items(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for k in (
            "items",
            "documents",
            "docs",
            "entries",
            "knowledge",
            "data",
            "results",
            "contexts",
            "files",
        ):
            v = payload.get(k)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
    return []


def pick_path(item: dict) -> str:
    # Prioritize explicit path fields
    for k in (
        "source",
        "source_path",
        "path",
        "file_path",
        "filepath",
        "relpath",
        "file",
    ):
        v = item.get(k)
        if isinstance(v, str) and v.strip():
            return v
    # nested metadata keys
    meta = item.get("metadata")
    if isinstance(meta, dict):
        for k in (
            "source",
            "source_path",
            "path",
            "file_path",
            "filepath",
            "relpath",
            "file",
        ):
            v = meta.get(k)
            if isinstance(v, str) and v.strip():
                return v
    return ""


def pick_field(item: dict, key: str) -> None:
    if key in item:
        return item.get(key)
    meta = item.get("metadata")
    if isinstance(meta, dict) and key in meta:
        return meta.get(key)
    return None


def load_expected() -> dict[str, dict]:
    raw = json.load(open(META_PATH, encoding="utf-8"))

    items = []
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        # Try standard keys
        if any(k in raw for k in ("items", "documents", "docs")):
            items = raw.get("items") or raw.get("documents") or raw.get("docs")
        else:
            # Assume it's a dict of items (Key -> Item)
            items = list(raw.values())

    if not isinstance(items, list):
        items = []

    out: dict[str, dict] = {}
    for m in items:
        if not isinstance(m, dict):
            continue
        p = ""
        for k in (
            "path",
            "file",
            "filepath",
            "file_path",
            "source_path",
            "relpath",
            "id",
            "key",
            "name",
            "title",
        ):
            v = m.get(k)
            if isinstance(v, str) and v.strip():
                p = v
                break
        if p:
            out[norm_path(p)] = m
    return out


def find_context7_endpoint(openapi: dict) -> str | None:
    paths = openapi.get("paths", {})
    if not isinstance(paths, dict):
        return None
    candidates = []
    for p, ops in paths.items():
        if not isinstance(p, str):
            continue
        if "context7" in p.lower() and isinstance(ops, dict) and "get" in ops:
            candidates.append(p)
    # prefer "list" endpoints
    for want in (
        "/api/context7/list",
        "/context7/list",
        "/api/context7/items",
        "/api/context7",
    ):
        if want in candidates:
            return want
    return candidates[0] if candidates else None


def main() -> int:
    if not os.path.exists(META_PATH):
        print(f"FAIL: missing metadata json: {META_PATH}")
        return 2

    expected = load_expected()
    if not expected:
        print("FAIL: expected metadata json loaded 0 items")
        return 2

    try:
        openapi = http_json(f"{BASE}/openapi.json")
    except Exception as e:
        print(f"WARN: could not load openapi.json: {e}")
        openapi = {}

    ep = find_context7_endpoint(openapi) if openapi else "/api/context7/list"
    if not ep:
        ep = "/api/context7/list"

    print(f"DEBUG: Using endpoint {ep}")

    try:
        payload = http_json(f"{BASE}{ep}")
    except Exception as e:
        print(f"FAIL: could not fetch context7 list: {e}")
        return 3

    items = extract_items(payload)
    if not items:
        print("FAIL: context7 endpoint returned 0 items")
        print("endpoint:", ep)
        return 3

    loaded_paths = set()
    for it in items:
        p = norm_path(pick_path(it))
        if p:
            loaded_paths.add(p)

    expected_paths = set(expected.keys())
    overlap = sorted(list(loaded_paths & expected_paths))

    print("=== CONTEXT7 REMOTE METADATA VERIFY (STRICT) ===")
    print("BASE:", BASE)
    print("endpoint:", ep)
    print("items_loaded:", len(items))
    print("expected_items_in_json:", len(expected))
    print("overlap_with_expected:", len(overlap))

    # 핵심 게이트 1: 원격이 JSON 수보다 적게 로드하면 FAIL (지금 케이스 잡기)
    if len(items) < len(expected):
        print("❌ FAIL: remote returned fewer items than JSON SSOT expects")
        print("hint: remote likely loaded only core knowledge (JSON/docs not loaded)")
        print("expected_sample:", list(expected_paths)[:5])
        print("loaded_sample:", sorted(list(loaded_paths))[:10])
        return 4

    # 핵심 게이트 2: 교집합이 0이면 FAIL (비교 자체가 불가능)
    if not overlap:
        print("❌ FAIL: no expected JSON doc paths found in remote context7 list")
        print("expected_sample:", list(expected_paths)[:10])
        print("loaded_sample:", sorted(list(loaded_paths))[:20])
        return 4

    mismatches = []
    missing_meta = []

    for p in overlap:
        it = None
        for cand in items:
            if norm_path(pick_path(cand)) == p:
                it = cand
                break
        if it is None:
            continue

        cat = pick_field(it, "category")
        tags = pick_field(it, "tags")
        desc = pick_field(it, "description")

        cat_s = cat.strip() if isinstance(cat, str) else None
        tags_set = set(as_list(tags))
        desc_s = desc.strip() if isinstance(desc, str) else None

        exp = expected[p]
        exp_cat = exp.get("category")
        exp_tags = exp.get("tags")
        exp_desc = exp.get("description")

        exp_cat_s = exp_cat.strip() if isinstance(exp_cat, str) else None
        exp_tags_set = set(as_list(exp_tags))
        exp_desc_s = exp_desc.strip() if isinstance(exp_desc, str) else None

        if cat_s is None and not tags_set and desc_s is None:
            missing_meta.append(p)
            continue

        if exp_cat_s is not None and cat_s != exp_cat_s:
            mismatches.append((p, "category", exp_cat_s, cat_s))
        if exp_tags_set and tags_set != exp_tags_set:
            mismatches.append((p, "tags", sorted(exp_tags_set), sorted(tags_set)))
        if exp_desc_s is not None and desc_s != exp_desc_s:
            mismatches.append((p, "description", exp_desc_s, desc_s))

    print("checked_overlap_items:", len(overlap))
    print("missing_metadata_on_expected_items:", len(missing_meta))
    print("mismatches:", len(mismatches))
    for row in mismatches[:50]:
        print("MISMATCH:", row[0], row[1], "expected=", row[2], "actual=", row[3])

    if missing_meta or mismatches:
        print("❌ FAIL: metadata not fully aligned")
        return 4

    print("✅ PASS: metadata aligned with JSON SSOT (strict)")
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        exit(1)
