# PH22-03: Chancellor V2 Cutover SSOT

## Goal

V2 Graph를 기본 엔진으로 전환하되, 운영 리스크 최소화.

---

## 3-Phase Cutover

### Phase 1: SHADOW (운영 영향 0)

| 항목 | 내용 |
|------|------|
| **응답** | V1 결과 반환 |
| **V2** | 백그라운드 실행 → diff 저장 |
| **저장 위치** | `artifacts/chancellor_shadow_diff/` |
| **실패 시** | V1 응답 유지, 메트릭만 기록 |

#### Shadow Diff 허용 범위 (SSOT)

| 항목 | 허용 | FAIL 기준 |
|------|------|-----------|
| **V2 성공률** | ≥99% | <99% → FAIL |
| **VerifyFail** | 0건/5분 | >0 → FAIL |
| **TraceGap** | 0건 | 60분 무응답 → FAIL |
| **sequential_thinking** | 항상 존재 | 누락 → FAIL |
| **context7** | 항상 존재 | 누락 → FAIL |
| **KINGDOM_DNA** | 항상 injected=true | false → FAIL |
| **KINGDOM_DNA content** | ≥100 chars | <100 → FAIL |
| **ExecuteBlocked** | 정상 패턴 | 급증 → WARNING |

**합격 기준:**
- [ ] V2 성공률 ≥ 99%
- [ ] VerifyFail/TraceGap 알람 0건
- [ ] sequential_thinking + context7 항상 존재
- [ ] KINGDOM_DNA injected + ≥100 chars

---

### Phase 2: CANARY (일부 트래픽만)

| 항목 | 내용 |
|------|------|
| **라우팅** | `X-AFO-Engine: v2` 헤더 |
| **대상** | 내부 사용자 / staging |
| **모니터링** | PH22-02 AlertManager |

**합격 기준:**
- [ ] Canary 기간 VerifyFail 급증 없음
- [ ] ExecuteBlocked 정상 패턴
- [ ] trace/checkpoint 정상 생성

---

### Phase 3: DEFAULT (V2 기본값)

| 항목 | 내용 |
|------|------|
| **전환** | V2를 기본 엔진으로 |
| **V1** | 삭제 (git revert로 롤백) |
| **롤백** | 배포 롤백으로만 (코드 경로 X) |

**합격 기준:**
- [ ] trace 생성 지속
- [ ] 알람 안정
- [ ] retention/prune 정상

---

## Hard Gates (필수)

1. **Kingdom DNA 출처 검증**
   - `library_id`가 `/afo-kingdom/`으로 시작하거나
   - 명시적 allowlist 라이브러리만 허용
   - 그 외 = 즉시 FAIL

2. **MCP 연결 검증**
   - Sequential Thinking + Context7 연결 필수
   - MCP 실패 = Graph 실행 실패

---

## Commands

```bash
# Shadow 검증
python scripts/chancellor_v2_integration_test.py
python scripts/chancellor_v2_contract_test.py

# Canary 라우팅 (staging)
export AFO_ENGINE_MODE=canary

# Default 전환
export AFO_ENGINE_MODE=default
```
