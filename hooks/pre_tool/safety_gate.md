---
hook_type: pre_tool
name: "safety_gate"
displayName: "이순신 안전 게이트 훅"
description: "도구 실행 전 위험 작업 감지 및 차단"
priority: 90
enabled: true
strategist: "이순신 (李舜臣)"
role: "善 Shield"
---

# 이순신 안전 게이트 훅 (Safety Gate Hook)

> "거북선의 수호로 시스템 안전성 보장"

도구 실행 전 위험한 작업을 감지하고, 필요시 차단하거나 확인을 요청합니다.

---

## 훅 정보

| 항목 | 값 |
|------|-----|
| **훅 타입** | pre_tool |
| **우선순위** | 90 |
| **전략가** | 이순신 (善 Shield) |
| **아이콘** | 🛡️ |

---

## 위험 키워드 탐지

### CRITICAL (즉시 차단)

| 키워드 | 위험도 | 설명 |
|--------|--------|------|
| `rm -rf /` | 10 | 루트 삭제 |
| `DROP DATABASE` | 10 | DB 삭제 |
| `--force --hard` | 9 | 강제 덮어쓰기 |
| `format` + `disk` | 9 | 디스크 포맷 |

### HIGH (사령관 승인 필요)

| 키워드 | 위험도 | 설명 |
|--------|--------|------|
| `delete` | 7 | 삭제 작업 |
| `drop` | 7 | 드롭 작업 |
| `production` | 8 | 프로덕션 환경 |
| `credential` | 8 | 인증 정보 |
| `secret` | 8 | 시크릿 |
| `password` | 8 | 패스워드 |
| `deploy` | 6 | 배포 |
| `migration` | 6 | 마이그레이션 |

### MEDIUM (경고 표시)

| 키워드 | 위험도 | 설명 |
|--------|--------|------|
| `remove` | 5 | 제거 |
| `destroy` | 5 | 파괴 |
| `truncate` | 5 | 잘라내기 |
| `overwrite` | 4 | 덮어쓰기 |

---

## 게이트 로직

```yaml
safety_gates:
  # 게이트 1: 즉시 차단
  critical_block:
    condition:
      risk_score: ">= 9"
    action: BLOCK
    message: "이순신 거부: 시스템 위험 작업 감지"

  # 게이트 2: 사령관 승인
  high_risk_approval:
    condition:
      risk_score: "6-8"
    action: ASK_COMMANDER
    message: "이순신 경고: 위험 작업 - 사령관 승인 필요"

  # 게이트 3: 경고 표시
  medium_risk_warning:
    condition:
      risk_score: "4-5"
    action: WARN_AND_PROCEED
    message: "이순신 주의: 신중히 진행하세요"

  # 게이트 4: 안전 통과
  safe_pass:
    condition:
      risk_score: "< 4"
    action: PASS
    message: "이순신 승인: 안전한 작업"
```

---

## 롤백 가능성 체크

```yaml
rollback_check:
  reversible:
    - git_operations: true  # git으로 복구 가능
    - file_edit: true       # 백업으로 복구 가능
    - test_run: true        # 영향 없음

  irreversible:
    - database_drop: false  # 복구 불가
    - file_delete: "partial"# 부분 복구
    - production_deploy: "complex"  # 복잡한 롤백
```

---

## 출력 형식

```yaml
safety_gate_result:
  tool: "[실행 도구]"
  command: "[명령어]"

  risk_analysis:
    keywords_found:
      - keyword: "[키워드]"
        severity: [CRITICAL/HIGH/MEDIUM/LOW]
        risk_score: [0-10]

    total_risk_score: [0-10]
    rollback_possible: [true/false/partial]

  decision:
    action: [BLOCK/ASK_COMMANDER/WARN/PASS]
    strategist: "이순신 (李舜臣)"

  message: "[결정 메시지]"

  mitigation:
    - "[완화 조치 1]"
    - "[완화 조치 2]"
```

---

## 예시

### CRITICAL 차단

```yaml
input:
  tool: Bash
  command: "rm -rf /"

output:
  risk_analysis:
    total_risk_score: 10
  decision:
    action: BLOCK
    strategist: "이순신 (李舜臣)"
  message: "🛡️ 이순신 거부: 루트 디렉토리 삭제 시도 차단"
```

### HIGH 승인 요청

```yaml
input:
  tool: Bash
  command: "deploy to production"

output:
  risk_analysis:
    keywords_found:
      - keyword: "production"
        severity: HIGH
        risk_score: 8
    total_risk_score: 8
  decision:
    action: ASK_COMMANDER
  message: "🛡️ 이순신 경고: 프로덕션 배포 - 사령관 승인 필요"
  mitigation:
    - "배포 전 스테이징 테스트 완료 확인"
    - "롤백 계획 준비"
```

---

## 이순신의 핵심 질문

> "최악의 경우 무슨 일이 발생하는가?"

모든 위험 작업에 대해 이 질문을 적용합니다:

1. **데이터 손실**: 복구 가능한가?
2. **서비스 중단**: 영향 범위는?
3. **보안 위협**: 노출 위험은?
4. **비용 증가**: 예상 비용은?

---

## 세종대왕의 정신

### 이순신 (李舜臣) - 거북선의 수호

> "거북선과 학익진으로 조국을 수호한 성웅"

- 시스템 안전성 최우선
- 리스크 사전 평가
- 롤백 가능성 항상 확보

---

## 관련 파일

- KeyTriggerRouter: `packages/afo-core/api/chancellor_v2/orchestrator/key_trigger_router.py`
- 安 게이트: `packages/afo-core/api/chancellor_v2/gates/safety_gate.py`
