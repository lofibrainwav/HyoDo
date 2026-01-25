---
description: "Trinity Score 계산 및 행동 결정"
allowed-tools: Read, Bash(git diff:*), Bash(git status:*), Bash(curl:*)
impact: CRITICAL
tags: [trinity, score, decision, 5pillars]
---

# Trinity Score 계산

$ARGUMENTS 작업에 대한 Trinity Score를 계산합니다.

## MCP 통합 (자동 계산)

Soul Engine이 실행 중인 경우 자동 계산:
```bash
curl -s http://localhost:8010/api/trinity/calculate \
  -H "Content-Type: application/json" \
  -d '{"task": "$ARGUMENTS", "context": {}}'
```

## 5기둥 평가 (0~100 각각)

### 眞 (Truth) - 35%

- [ ] 구현이 정확한가?
- [ ] 기존 패턴을 따르는가?
- [ ] 타입이 안전한가?

### 善 (Goodness) - 35%

- [ ] 테스트가 있는가?
- [ ] CI가 통과하는가?
- [ ] 부작용이 없는가?

### 美 (Beauty) - 20%

- [ ] 코드가 깔끔한가?
- [ ] 린트를 통과하는가?
- [ ] 중복이 없는가?

### 孝 (Serenity) - 8%

- [ ] UX 영향이 적은가?
- [ ] 에러 메시지가 명확한가?
- [ ] 원샷 실행 가능한가?

### 永 (Eternity) - 2%

- [ ] 문서화되었는가?
- [ ] Evidence가 있는가?
- [ ] 롤백 가능한가?

## 계산 공식

```
total = (眞 * 0.35) + (善 * 0.35) + (美 * 0.20) + (孝 * 0.08) + (永 * 0.02)
```

## 행동 결정

| 조건 | 행동 |
| :--- | :--- |
| **Trinity >= 90 AND Risk <= 10** | **AUTO_RUN** (즉시 승인) |
| **Trinity >= 75 AND Risk <= 25** | **ASK_COMMANDER** (사령관 확인 필요) |
| **Trinity < 70 OR Risk > 30** | **BLOCK** (기술적/철학적 차단) |
| **Secrets/Auth 영향 감지** | **CRITICAL_BLOCK** (이순신 방패) |

## 출력 형식

```yaml
trinity_score:
  total: [점수]/100
  pillars:
    眞: [점수] # 근거
    善: [점수] # 근거
    美: [점수] # 근거
    孝: [점수] # 근거
    永: [점수] # 근거
  risk_score: [점수]/100
  decision: [AUTO_RUN | ASK_COMMANDER | BLOCK]
```
