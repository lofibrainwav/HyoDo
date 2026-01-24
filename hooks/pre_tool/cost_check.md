---
hook_type: pre_tool
name: "cost_check"
displayName: "비용 티어 체크 훅"
description: "도구 실행 전 비용 티어를 확인하고 FREE 우선 라우팅"
priority: 100
enabled: true
---

# 비용 티어 체크 훅 (Cost Check Hook)

> "장영실의 측우기처럼 정확한 비용 측정"

도구 실행 전 작업의 비용 티어를 확인하고, 가능하면 FREE 티어(Ollama)로 라우팅합니다.

---

## 훅 정보

| 항목 | 값 |
|------|-----|
| **훅 타입** | pre_tool |
| **우선순위** | 100 (최우선) |
| **활성화** | true |

---

## 비용 티어 정의

| 티어 | 모델 | 비용 | 트리거 |
|------|------|------|--------|
| **FREE** | qwen3:8b (Ollama) | $0.000/1k | debug, lint, test, simple |
| **CHEAP** | claude-haiku-4-5 | $0.00025/1k | implement, refactor |
| **EXPENSIVE** | claude-opus-4-5 | $0.015/1k | design, architect, complex |

---

## 라우팅 로직

```yaml
routing_rules:
  # 규칙 1: FREE 우선
  - condition:
      task_type:
        - debug
        - lint
        - test
        - type_check
        - simple_fix
    action: route_to_ollama
    tier: FREE
    savings: "100%"

  # 규칙 2: 복잡도 기반
  - condition:
      complexity: "<= 3"
      no_dangerous_keywords: true
    action: route_to_haiku
    tier: CHEAP
    savings: "98%"

  # 규칙 3: 위험 작업
  - condition:
      dangerous_keywords:
        - delete
        - drop
        - production
        - credential
    action: route_to_opus_with_confirmation
    tier: EXPENSIVE
    require_approval: true

  # 규칙 4: 복잡한 설계
  - condition:
      complexity: "> 5"
      keywords:
        - architect
        - design
        - complex
    action: route_to_opus
    tier: EXPENSIVE
```

---

## 복잡도 계산

```yaml
complexity_factors:
  # 파일 수
  files_affected:
    1: +0
    2-3: +1
    4-10: +2
    ">10": +3

  # 코드 라인
  lines_changed:
    "<50": +0
    "50-200": +1
    "200-500": +2
    ">500": +3

  # 키워드
  keywords:
    simple: -1
    refactor: +1
    architect: +2
    complex: +2
    production: +2
```

---

## 출력 형식

```yaml
cost_check_result:
  tool: "[실행 도구]"
  task: "[작업 내용]"

  analysis:
    complexity_score: [0-10]
    dangerous_keywords: [키워드 목록]
    files_affected: [파일 수]

  routing_decision:
    tier: [FREE/CHEAP/EXPENSIVE]
    model: "[모델명]"
    estimated_cost: "$[예상 비용]"
    savings_vs_opus: "[절감률]%"

  approval_required: [true/false]
  recommendation: "[권고사항]"
```

---

## 예시

### FREE 티어 라우팅

```yaml
input:
  tool: Bash
  command: "pytest tests/"

output:
  routing_decision:
    tier: FREE
    model: "ollama/qwen3:8b"
    estimated_cost: "$0.00"
    savings_vs_opus: "100%"
  recommendation: "테스트 실행은 오호대장군(조운)에게 위임"
```

### EXPENSIVE 티어 (승인 필요)

```yaml
input:
  tool: Bash
  command: "deploy to production"

output:
  routing_decision:
    tier: EXPENSIVE
    model: "claude-opus-4-5"
    estimated_cost: "$0.15"
  approval_required: true
  recommendation: "프로덕션 배포 - 이순신(善) 승인 필요"
```

---

## 세종대왕의 정신

### 장영실 (眞) - 측우기의 정밀함

> "필요한 것만 정확하게 측정하라"

- 비용을 정밀하게 예측
- 불필요한 EXPENSIVE 호출 방지
- 토큰 버닝 최적화

---

## 관련 파일

- CostAwareRouter: `packages/afo-core/api/chancellor_v2/orchestrator/cost_aware_router.py`
- 비용 설정: `packages/afo-core/api/chancellor_v2/config/cost_config.yaml`
