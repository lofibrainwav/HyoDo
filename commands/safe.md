---
description: "[Simple] 코드 안전성 검사 - 보안/리스크 체크"
allowed-tools: Read, Glob, Grep, Bash(git diff:*)
impact: LOW
tags: [simple, safety, security, beginner]
mode: simple
alias: strategist
---

# /safe - 안전성 검사

코드의 안전성을 검사합니다. (Advanced: `/strategist`)

## 사용법

```
/safe               # 현재 변경사항 검사
/safe "파일명"      # 특정 파일 검사
```

## 검사 항목

| 항목 | 체크 내용 |
|------|----------|
| 비밀키 | API 키, 패스워드 노출 |
| 위험 명령 | rm -rf, DROP TABLE 등 |
| 프로덕션 영향 | DB 변경, 설정 수정 |
| 롤백 가능 | 되돌릴 수 있는가? |

## 결과 예시

```
안전성 검사 결과:

✅ 비밀키 노출: 없음
✅ 위험 명령: 없음
⚠️ 프로덕션 영향: DB 스키마 변경 감지
✅ 롤백 가능: 마이그레이션 파일 있음

위험도: 낮음 (15/100)
→ 확인 후 진행 권장
```

## 위험도 레벨

| 위험도 | 의미 | 행동 |
|--------|------|------|
| 0-10 | 안전 | 바로 진행 |
| 11-30 | 주의 | 확인 후 진행 |
| 31+ | 위험 | 리뷰 필수 |

---

*상세 분석이 필요하면 `/strategist` 명령어를 사용하세요.*
