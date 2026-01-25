import json
import os

import requests

BASE = os.environ.get("AFO_BASE_URL", "http://localhost:8010").rstrip("/")
S = requests.Session()
S.headers.update({"accept": "application/json"})


def get_json(url: str) -> None:
    r = S.get(url, timeout=10)
    return r.status_code, r.headers.get("content-type", ""), r.text


def post_json(url: str, payload: dict) -> None:
    r = S.post(url, json=payload, timeout=20)
    return r.status_code, r.headers.get("content-type", ""), r.text


def main() -> None:
    urls = [
        f"{BASE}/api/health/comprehensive",
        f"{BASE}/api/skills",
    ]
    print(f"[base] {BASE}")

    for u in urls:
        sc, ct, body = get_json(u)
        print(f"[GET] {u} -> {sc} {ct}")
        if sc != 200:
            print(body[:800])
            return 1

    sc, ct, body = get_json(f"{BASE}/api/skills")
    data = None
    try:
        data = json.loads(body)
    except Exception:
        print("[err] /api/skills returned non-json")
        print(body[:800])
        return 1

    skills = data.get("skills") if isinstance(data, dict) else None
    if not skills:
        print(
            "[err] no skills list found in /api/skills payload keys:",
            list(data.keys()) if isinstance(data, dict) else type(data),
        )
        return 1

    skill_id = os.environ.get("SKILL_ID")
    if not skill_id:
        first = skills[0]
        skill_id = first.get("skill_id") or first.get("id") or first.get("name")
    if not skill_id:
        print("[err] could not infer a skill_id")
        return 1

    print("[pick] skill_id =", skill_id)

    execute_candidates = [
        (f"{BASE}/api/skills/execute", {"skill_id": skill_id, "args": {}}),
        (f"{BASE}/api/skills/execute", {"skill_id": skill_id, "input": {}}),
        (f"{BASE}/api/skills/execute", {"skill_id": skill_id, "params": {}}),
        (f"{BASE}/api/skills/execute", {"id": skill_id, "args": {}}),
    ]

    for url, payload in execute_candidates:
        sc, ct, body = post_json(url, payload)
        print(f"[POST] {url} payload_keys={list(payload.keys())} -> {sc} {ct}")
        if sc == 200:
            print(body[:1200])
            return 0
        print(body[:400])

    print("[warn] execute endpoint shape differs. Above attempts show exact server responses.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
