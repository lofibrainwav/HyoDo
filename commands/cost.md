---
description: "[Simple] AI 작업 비용 예측"
allowed-tools: Read
impact: LOW
tags: [simple, cost, beginner]
mode: simple
alias: cost-estimate
---

# /cost - 비용 예측

AI 작업의 예상 비용을 알려줍니다. (Advanced: `/cost-estimate`)

## 사용법

```
/cost "작업 설명"
```

## 비용 티어

| 티어 | 비용 | 사용 시점 |
|------|------|----------|
| FREE | $0 | 간단한 작업 (로컬 AI) |
| CHEAP | $0.0003/1k | 보통 작업 |
| EXPENSIVE | $0.015/1k | 복잡한 작업 |

## 결과 예시

```
/cost "버그 수정"

예상 비용: FREE ($0.00)
추천 모델: Ollama (로컬)
이유: 단순 디버깅 작업
```

```
/cost "새 기능 설계"

예상 비용: EXPENSIVE (~$0.15)
추천 모델: Claude Opus
이유: 아키텍처 결정 필요
```

## 비용 절감 팁

1. 간단한 작업은 `/cost` 먼저 확인
2. FREE 티어 가능하면 로컬 AI 사용
3. 복잡한 작업만 고급 모델 사용

---

*상세 비용 분석은 `/cost-estimate` 명령어를 사용하세요.*
