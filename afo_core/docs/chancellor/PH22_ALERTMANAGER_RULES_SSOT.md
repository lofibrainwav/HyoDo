# PH22 — Chancellor V2 AlertManager Rules SSOT

## Goal

Chancellor V2 운영에 필요한 핵심 알람을 Prometheus AlertManager에 추가한다.

---

## 알람 목록

| 알람 | 조건 | 심각도 | 설명 |
|------|------|--------|------|
| **ChancellorVerifyFail** | VERIFY fail > 5/5min | warning | 검증 실패 급증 |
| **ChancellorExecuteBlocked** | 403 blocked > 10/5min | warning | Allowlist 차단 급증 |
| **ChancellorTraceGap** | 60분간 trace 없음 | critical | 그래프 실행 중단 |
| **ChancellorArtifactsDiskHigh** | artifacts > 1GB | warning | 디스크 사용 과다 |

---

## 메트릭 노출 필요

V2 runner에서 다음 Prometheus 메트릭 노출 필요:

```python
# api/chancellor_v2/metrics.py
chancellor_v2_verify_fail_total = Counter(...)
chancellor_v2_execute_blocked_total = Counter(...)
chancellor_v2_trace_created_total = Counter(...)
```

---

## 적용 방법

`alertmanager-rules.yaml`에 아래 규칙 추가 후 Prometheus reload
