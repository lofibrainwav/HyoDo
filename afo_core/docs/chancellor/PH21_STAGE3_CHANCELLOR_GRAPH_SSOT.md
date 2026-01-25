# PH21 Stage 3 — Chancellor Graph SSOT (1-page)

## Goal

Chancellor Graph orchestration을 **"계약(Contract) + 체크포인트(Checkpoint) + 이벤트(Event)"**로 봉인한다.
Stage 2 Skills Allowlist 정책을 Graph 실행 경로에서 우회 불가로 유지한다.

## Non-Goals

- 기존 런타임(현 Graph/Router/Skill 호출 경로) 변경 금지 (V2는 side-by-side)
- 신규 외부 인프라 도입 금지 (파일 기반 아티팩트만)

---

## Nodes (V2 Canon)

```
CMD → PARSE → (TRUTH, GOODNESS, BEAUTY) → MERGE → EXECUTE → VERIFY → (ROLLBACK|REPORT)
```

| Node | 역할 | 기둥 |
|------|------|------|
| CMD | 사령관 요청 수신 | 孝 |
| PARSE | 의도 파싱 | 眞 |
| TRUTH | 기술 검증 (제갈량) | 眞 |
| GOODNESS | 윤리/안정성 검토 (사마의) | 善 |
| BEAUTY | UX/서사 관점 (주유) | 美 |
| MERGE | 3책사 종합 | 眞善美 |
| EXECUTE | 실행 (Stage 2 guard 경유) | 眞 |
| VERIFY | 검증 | 善 |
| ROLLBACK | 실패 시 복원 | 善 |
| REPORT | 결과 보고 | 孝 |

---

## State Schema (minimal)

```python
@dataclass
class GraphState:
    trace_id: str
    request_id: str
    input: dict[str, Any]
    plan: dict[str, Any]
    outputs: dict[str, Any]
    errors: list[str]
    step: str
    started_at: float
    updated_at: float
```

---

## Checkpoint Policy

- **저장 시점**: node 종료마다 checkpoint 1개 저장
- **저장 위치**: `artifacts/chancellor_checkpoints/{trace_id}/{step}.json`
- **원자적 쓰기**: tmp → replace (corruption 방지)

---

## Retry Policy

| 조건 | 동작 |
|------|------|
| node 실패 | 최대 3회 재시도 |
| backoff | 0.5s → 1.0s → 2.0s |
| VERIFY 실패 | **즉시 ROLLBACK 전환** (재시도 금지) |

---

## Rollback Policy

- VERIFY 실패 시 마지막 성공 checkpoint로 복원
- ROLLBACK은 **"부작용 제거"만** 수행 (overwrite 금지)

---

## Event Schema (jsonl)

- **위치**: `artifacts/chancellor_events/{trace_id}.jsonl`
- **필드**: `ts`, `trace_id`, `step`, `event`, `ok`, `detail`(optional)

---

## Security Constraints

1. Stage 2 Allowlist 정책을 우회하는 skill invocation 경로 **금지**
2. V2 EXECUTE는 반드시 **기존 runtime guard**를 경유한다 (직접 호출 금지)

---

## Success Criteria

- [ ] smoke 실행 시 events(jsonl) + checkpoints(json) 생성
- [ ] VERIFY 성공/실패 경로가 결정론적으로 재현됨

---

## Rollback (V2 제거)

```bash
rm -rf api/chancellor_v2
```

→ 완전 롤백 가능 (기존 런타임 영향 0)
