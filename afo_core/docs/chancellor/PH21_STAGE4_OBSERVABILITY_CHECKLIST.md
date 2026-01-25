# PH21 Stage 4 — Observability & Scaling Checklist

## Goal
배포/관찰/테스트를 자동화해서 운영 피로 감소

---

## 가시성 유지 체크리스트

| 항목 | 도구 | 상태 |
|------|------|------|
| **로그** | SSE Stream | ✅ 기존 구현 |
| **이벤트** | Chancellor V2 Events (JSONL) | ✅ 구현 완료 |
| **체크포인트** | Chancellor V2 Checkpoints (JSON) | ✅ 구현 완료 |
| **관찰 도구** | observability.py | ✅ 구현 완료 |
| **메트릭** | Prometheus | ✅ 기존 구현 |
| **대시보드** | Grafana (3100) | ✅ 운영 중 |
| **알림** | AlertManager | 🔜 다음 단계 |

---

## 자동화 파이프라인

```
Backup → Check → Execute → Verify → Report
   ↓        ↓        ↓         ↓        ↓
  永       眞       美        善       孝
```

### 현재 구현 상태
- ✅ **Checkpoint (永)**: 각 노드 완료 시 자동 저장
- ✅ **Event Log (眞)**: 모든 enter/exit/error 기록
- ✅ **Stage 2 Guard (善)**: 403 enforcement
- ✅ **VERIFY (善)**: PASS/FAIL 판정
- ✅ **ROLLBACK (善)**: checkpoint 복원

---

## CI Gate Scripts

| 스크립트 | 용도 |
|----------|------|
| `scripts/check_skills_allowlist.py` | Allowlist 구조 검증 |
| `scripts/chancellor_v2_smoke.py` | V2 기본 기능 검증 |
| `scripts/chancellor_v2_integration_test.py` | Stage 2 통합 검증 |

---

## 사용법

```bash
# 최근 trace 조회
python -c "from api.chancellor_v2.observability import *; print(format_trace_timeline(list_traces()[-1]))"

# trace 요약
python -c "from api.chancellor_v2.observability import *; print(format_trace_summary(list_traces()[-1]))"
```
