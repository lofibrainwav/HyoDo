# Security Policy

> "이순신의 거북선처럼 시스템을 수호한다"

## 이순신 (善 Shield) 보안 원칙

HyoDo는 이순신 전략가의 원칙에 따라 보안을 최우선으로 합니다.

### 핵심 질문

> "최악의 경우 무슨 일이 발생하는가?"

모든 보안 결정에서 이 질문을 적용합니다.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 3.0.x   | ✅ |
| 2.0.x   | ✅ |
| 1.0.x   | ❌ |

## Reporting a Vulnerability

### 보고 방법

1. **이메일**: security@afo.kingdom (존재하지 않음 - Issue 사용)
2. **GitHub Issue**: Private vulnerability report 사용

### 보고 내용

```yaml
vulnerability_report:
  title: "[보안] 취약점 제목"
  severity: [CRITICAL/HIGH/MEDIUM/LOW]
  description: "상세 설명"
  reproduction_steps:
    - "재현 단계 1"
    - "재현 단계 2"
  impact: "영향 범위"
  suggested_fix: "제안 수정안"
```

## 보안 게이트 (safety_gate.md)

HyoDo는 `safety_gate` 훅을 통해 위험한 작업을 자동으로 감지하고 차단합니다.

### CRITICAL 키워드 (즉시 차단)

- `rm -rf /`
- `DROP DATABASE`
- `--force --hard`

### HIGH 키워드 (승인 필요)

- `delete`, `drop`
- `production`
- `credential`, `secret`, `password`
- `deploy`, `migration`

## 안전한 사용

### DO

- 오호대장군 (FREE 티어) 활용
- `/preflight` 실행 후 커밋
- `/check` 품질 게이트 통과

### DON'T

- 프로덕션에 직접 배포
- 민감한 정보 하드코딩
- 테스트 없이 머지

---

*"거북선의 수호: 시스템 안전성 최우선"*
