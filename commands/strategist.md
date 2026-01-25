---
description: "세종대왕의 정신 - 3 전략가 관점으로 분석 (장영실/이순신/신사임당)"
allowed-tools: Read, Glob, Grep, Bash(curl:*)
impact: HIGH
tags: [strategist, analysis, trinity, decision, sejong]
---

# 세종대왕의 정신 - 3 Strategists 분석

$ARGUMENTS 에 대해 조선의 3대 위인 관점으로 분석합니다.

---

## 장영실 (蔣英實) - 眞 Sword ⚔️

> "측우기와 자격루를 만든 조선 최고의 과학자"

**역할**: 기술적 정확성, 아키텍처, 검증

### 분석 포인트

- 기술적으로 올바른가?
- 아키텍처 원칙을 따르는가?
- 장기적 확장성은?
- 타입 안전성이 보장되는가?

### 핵심 질문

- "이 설계가 3년 후에도 유효한가?"
- "기술 부채가 발생하는가?"
- "테스트 커버리지는 충분한가?"

---

## 이순신 (李舜臣) - 善 Shield 🛡️

> "거북선과 학익진으로 조국을 수호한 성웅"

**역할**: 안전성, 리스크 평가, 게이트키핑

### 분석 포인트

- 안전한가?
- 리스크는 무엇인가?
- 롤백 가능한가?
- 보안 취약점은 없는가?

### 핵심 질문

- "최악의 경우 무슨 일이 발생하는가?"
- "테스트가 충분한가?"
- "프로덕션에 영향을 미치는가?"

---

## 신사임당 (申師任堂) - 美 Bridge 🌉

> "초충도와 묵죽도의 예술혼을 담은 현모양처"

**역할**: UX, 가독성, 커뮤니케이션, 인지 부하 감소

### 분석 포인트

- 사용자 경험은 어떤가?
- 코드가 읽기 쉬운가?
- 에러 메시지가 명확한가?
- 문서화가 충분한가?

### 핵심 질문

- "사용자가 이해할 수 있는가?"
- "복잡성을 숨길 수 있는가?"
- "인지 부하가 최소화되었는가?"

---

## 통합 판단

```yaml
strategist_analysis:
  task: "$ARGUMENTS"
  philosophy: "세종대왕의 정신"

  jang_yeong_sil:  # 眞 Sword ⚔️
    verdict: [APPROVE | CONCERN | REJECT]
    reason: "[설명]"
    tech_debt_score: [0-100]

  yi_sun_sin:  # 善 Shield 🛡️
    verdict: [APPROVE | CONCERN | REJECT]
    reason: "[설명]"
    risk_score: [0-100]

  shin_saimdang:  # 美 Bridge 🌉
    verdict: [APPROVE | CONCERN | REJECT]
    reason: "[설명]"
    ux_friction: [0-100]

  consensus: [UNANIMOUS | MAJORITY | BLOCKED]
  final_decision: [AUTO_RUN | ASK_COMMANDER | BLOCK]
```

## 결정 기준

- **UNANIMOUS APPROVE**: AUTO_RUN 가능 (세 전략가 모두 승인)
- **MAJORITY APPROVE**: ASK_COMMANDER (2명 승인, 1명 우려)
- **ANY REJECT**: BLOCK (한 명이라도 거부)

---

## 세종대왕의 정신 통합

```text
┌─────────────────────────────────────────────────────┐
│              세종대왕의 정신 (世宗大王)                │
│  "백성을 위한 실용적 혁신과 문화적 융성"              │
├─────────────────────────────────────────────────────┤
│                                                     │
│   ⚔️ 장영실 (眞)     🛡️ 이순신 (善)    🌉 신사임당 (美)  │
│   측우기의 정밀함     거북선의 수호     초충도의 예술   │
│                                                     │
│   기술적 정확성      안전성 보장       UX 우수성      │
│   검증 가능성        리스크 최소화     가독성 확보    │
│   아키텍처 일관성    롤백 가능성       문서화 품질    │
│                                                     │
└─────────────────────────────────────────────────────┘
```
