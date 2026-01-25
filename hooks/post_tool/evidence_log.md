---
hook_type: post_tool
name: "evidence_log"
displayName: "결정 증거 기록 훅"
description: "도구 실행 후 결정 증거를 자동으로 기록"
priority: 80
enabled: true
---

# 결정 증거 기록 훅 (Evidence Log Hook)

> "장영실의 측우기처럼 모든 결정을 정밀하게 기록한다"

도구 실행 후 결정 과정과 결과를 자동으로 기록하여 추적 가능성을 확보합니다.

---

## 훅 정보

| 항목 | 값 |
|------|-----|
| **훅 타입** | post_tool |
| **우선순위** | 80 |
| **활성화** | true |

---

## 기록 항목

### 필수 항목

```yaml
evidence_record:
  timestamp: "[ISO 8601]"
  session_id: "[세션 ID]"

  tool:
    name: "[도구명]"
    parameters: "[파라미터]"

  execution:
    status: [success/failure]
    duration_ms: [실행 시간]
    output_summary: "[출력 요약]"
```

### 전략가 판단 기록

```yaml
strategist_decision:
  jang_yeong_sil:  # 眞 Sword
    evaluated: [true/false]
    verdict: [APPROVE/CONCERN/REJECT]
    tech_debt_score: [0-100]

  yi_sun_sin:  # 善 Shield
    evaluated: [true/false]
    verdict: [APPROVE/CONCERN/REJECT]
    risk_score: [0-100]

  shin_saimdang:  # 美 Bridge
    evaluated: [true/false]
    verdict: [APPROVE/CONCERN/REJECT]
    ux_friction: [0-100]
```

### 오호대장군 기록

```yaml
generals_deployment:
  deployed: [true/false]
  generals_used:
    - name: "[장군명]"
      model: "[모델]"
      task: "[수행 작업]"
      result: "[결과]"
  total_cost: "$0.00"
```

---

## 저장 위치

```
.claude/
├── evidence/
│   ├── 2026-01-24/
│   │   ├── session_001.yaml
│   │   ├── session_002.yaml
│   │   └── ...
│   └── summary/
│       └── daily_summary.yaml
```

---

## 출력 형식

```yaml
evidence_log_result:
  hook: "evidence_log"
  status: [recorded/skipped]

  record:
    id: "[증거 ID]"
    file: "[저장 파일 경로]"

  summary:
    tool: "[도구명]"
    status: "[실행 상태]"
    strategists_consulted: [수]
    generals_deployed: [수]
    cost_tier: "[FREE/CHEAP/EXPENSIVE]"

  message: "[기록 메시지]"
```

---

## 예시

### 성공 기록

```yaml
evidence_log_result:
  status: recorded

  record:
    id: "EV-2026-01-24-001"
    file: ".claude/evidence/2026-01-24/session_001.yaml"

  summary:
    tool: "Bash"
    status: "success"
    strategists_consulted: 2
    generals_deployed: 1
    cost_tier: "FREE"

  message: "pytest 실행 증거 기록 완료"
```

---

## 세종대왕의 정신

### 장영실 (眞) - 측우기의 정밀함

> "모든 것을 측정하고 기록하라"

- 실행 결과의 정밀한 기록
- 재현 가능한 증거 확보
- 기술 부채 추적

---

## 관련 파일

- 증거 저장소: `.claude/evidence/`
- 증거 명령어: `.claude/commands/evidence.md`
