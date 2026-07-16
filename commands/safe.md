---
description: "[Simple] 코드 안전성 검사 - 보안/리스크 체크"
allowed-tools: Read, Glob, Grep, Bash(git diff:*), Bash(hyodo:*)
impact: LOW
tags: [simple, safety, security, beginner]
mode: simple
alias: strategist
---

# /safe - 안전성 검사

변경 내용에서 **고위험 신호**를 먼저 찾습니다. (Advanced: `/strategist`)

`/safe` 와 `hyodo safe` 는 초기 경보(early warning)입니다. 완전한 보안 스캐너·SAST·의존성 감사·사람 보안 리뷰를 대체하지 않습니다.

## 사용법

Agent slash command:

```text
/safe
/safe "파일명"
```

벤더 무관 CLI:

```bash
hyodo safe
hyodo safe path/to/file_or_dir
hyodo safe --strict
```

## 검사 항목

| 항목 | 체크 내용 |
|------|----------|
| 비밀키 | API 키·토큰·private key 패턴 |
| 위험 명령 | `rm -rf`, `DROP DATABASE`, force push 등 |
| 프로덕션 영향 | migration, deploy, schema 변경 신호 |
| 롤백 힌트 | rollback/migration 문구 존재 여부 (보증 아님) |

## 기본 동작

1. 경로가 있으면 해당 파일/디렉터리를 읽습니다.
2. 경로가 없으면 `git diff HEAD` (없으면 `git status`)를 스캔합니다.
3. 매칭 결과를 위험도 점수와 함께 출력합니다.

## 결과 예시

```text
안전성 검사 결과:
source: git diff HEAD

✅ 비밀키 노출
✅ 위험 명령
⚠️ 프로덕션 영향
✅ 롤백 가능성

위험도: 주의 (15/100)
→ 확인 후 진행 권장
```

## 위험도 레벨

| 위험도 | 의미 | 행동 |
|--------|------|------|
| 0-10 | 낮음 | 진행 가능 후보 — 최종 승인은 사람 |
| 11-30 | 주의 | 확인 후 진행 |
| 31+ | 위험 | 리뷰 필수 |

---

*상세 분석이 필요하면 `/strategist` 또는 `SECURITY.md` 를 참고하세요.*
