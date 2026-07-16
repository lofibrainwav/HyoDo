---
description: "[Simple] HyoDo 시작 가이드 - 처음 사용자용"
allowed-tools: Read
impact: LOW
tags: [simple, help, beginner, onboarding]
mode: simple
---

# /start - HyoDo quick start

HyoDo is a Claude Code quality gate and cost-aware review kit for AI-assisted
developers. It helps you inspect AI-generated changes before you trust them.

Start practical. Philosophy and advanced scoring are optional layers after the
basic review loop works.

## 핵심 명령어 5개

| 명령어 | 기능 | 예시 |
| :--- | :--- | :--- |
| `/check` | 코드 품질 체크 | `/check` |
| `/score` | 품질 점수 확인 | `/score` |
| `/safe` | 안전성 검사 | `/safe` |
| `/cost` | 비용 예측 | `/cost "작업"` |
| `/start` | 이 도움말 | `/start` |

## 30-second quick start

```bash
1. /check          # quality gates
2. /score          # review score
3. /safe           # safety-oriented review
4. fix or escalate
```

## Score system

```text
F >= 54 and S >= 8  -> strong candidate after human review
F >= 45 and S >= 7  -> review recommended
F < 45              -> fix before merge
```

## 더 알고 싶다면

| 레벨 | 명령어 | 설명 |
| :--- | :--- | :--- |
| 초급 | `/check`, `/score`, `/safe` | 기본 기능 |
| 중급 | `/trinity`, `/strategist` | 상세 분석 |
| 고급 | `/chancellor-v3`, `/ultrawork` | 전체 시스템 |

## HyoDo란?

- **Code quality** gates for AI-assisted changes
- **Cost-aware routing** to avoid unnecessary premium-model usage
- **Safety review** before risky changes are trusted

Scores support review. They do not replace tests, security review, or human
judgment. Start with `/check`.

---

*고급 기능: `/trinity`, `/strategist`, `/organs`, `/ultrawork`*
