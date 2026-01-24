---
description: "AFO 10초 프로토콜 - 작업 전 필수 점검"
allowed-tools: Read, Glob, Grep, Bash(git status:*), Bash(git log:*), Bash(git diff:*)
impact: CRITICAL
tags: [preflight, protocol, ssot, planning]
---

# AFO 10초 프로토콜 실행

$ARGUMENTS 작업을 시작하기 전에 10초 프로토콜을 실행합니다.

## 체크리스트

1. **SSOT 확인** (존재하는 것만):
   - docs/AFO_ROYAL_LIBRARY.md
   - docs/AFO_CHANCELLOR_GRAPH_SPEC.md
   - AGENTS.md

2. **현재 상태 파악**:
   - git status로 변경된 파일 확인
   - 관련 코드 영역의 기존 패턴 파악

3. **10초 프로토콜 출력 형식**:

```
decision: AUTO_RUN | ASK_COMMANDER | BLOCK
evidence: [SSOT 1개 + 코드/로그 1개]
plan: [3 steps 이내]
checks_to_run: lint | type | tests | build
rollback_plan: [git 기반 되돌리기]
```

## Trinity Score 계산

- 眞 (Truth) 35%: 구현 정확성
- 善 (Goodness) 35%: 안정성/테스트
- 美 (Beauty) 20%: 코드 품질
- 孝 (Serenity) 8%: 사용자 영향
- 永 (Eternity) 2%: 문서화/기록

## Risk Score 기준

- Auth/Payment/Secrets: +60
- DB/데이터 변경: +40
- 의존성 변경: +30
- 테스트 없는 핵심 로직: +25
- 문서/UI: +5~10

**AUTO_RUN**: Trinity >= 90 AND Risk <= 10
**그 외**: ASK_COMMANDER
