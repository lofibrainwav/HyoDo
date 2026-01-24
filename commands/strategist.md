---
description: "3 Strategists 관점으로 분석 (제갈량/사마의/주유)"
allowed-tools: Read, Glob, Grep, Bash(curl:*)
impact: HIGH
tags: [strategist, analysis, trinity, decision]
---

# 3 Strategists 분석

$ARGUMENTS 에 대해 3명의 전략가 관점으로 분석합니다.

## Zhuge Liang (諸葛亮) - 眞 Sword ⚔️
**역할**: 아키텍처, 전략, 기술적 확신

### 분석 포인트

- 기술적으로 올바른가?
- 아키텍처 원칙을 따르는가?
- 장기적 확장성은?

### 질문

- "이 설계가 3년 후에도 유효한가?"
- "기술 부채가 발생하는가?"

---

## Sima Yi (司馬懿) - 善 Shield 🛡️
**역할**: 윤리, 안정성, 리스크 평가, 게이트키핑

### 분석 포인트

- 안전한가?
- 리스크는 무엇인가?
- 롤백 가능한가?

### 질문

- "최악의 경우 무슨 일이 발생하는가?"
- "테스트가 충분한가?"

---

## Zhou Yu (周瑜) - 美 Bridge 🌉
**역할**: 내러티브, UX, 커뮤니케이션, 인지 부하 감소

### 분석 포인트

- 사용자 경험은 어떤가?
- 코드가 읽기 쉬운가?
- 에러 메시지가 명확한가?

### 질문

- "사용자가 이해할 수 있는가?"
- "복잡성을 숨길 수 있는가?"

---

## 통합 판단

```yaml
strategist_analysis:
  task: "$ARGUMENTS"

  zhuge_liang:  # 眞 Sword
    verdict: [APPROVE | CONCERN | REJECT]
    reason: "[설명]"

  sima_yi:  # 善 Shield
    verdict: [APPROVE | CONCERN | REJECT]
    reason: "[설명]"
    risk_score: [0-100]

  zhou_yu:  # 美 Bridge
    verdict: [APPROVE | CONCERN | REJECT]
    reason: "[설명]"
    ux_friction: [0-100]

  consensus: [UNANIMOUS | MAJORITY | BLOCKED]
  final_decision: [AUTO_RUN | ASK_COMMANDER | BLOCK]
```

## 결정 기준

- **UNANIMOUS APPROVE**: AUTO_RUN 가능
- **MAJORITY APPROVE**: ASK_COMMANDER
- **ANY REJECT**: BLOCK
