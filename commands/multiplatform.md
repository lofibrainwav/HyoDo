---
description: "멀티플랫폼 오케스트레이션 - Claude/Ollama/Codex/OpenCode 라우팅"
allowed-tools: Read, Grep, Bash(curl:*)
impact: MEDIUM
tags: [multiplatform, orchestration, routing, cost-optimization]
---

# /multiplatform - 멀티플랫폼 오케스트레이션

> "세종대왕이 지휘하고, 각 플랫폼이 역할에 맞게 실행한다"

$ARGUMENTS 작업을 분석하여 최적의 플랫폼(Claude/Ollama/Codex/OpenCode)으로 라우팅합니다.

---

## 플랫폼 계층 구조

```
┌─────────────────────────────────────────────────────┐
│           Chancellor V3 (총괄 오케스트레이터)          │
│     CostAwareRouter + KeyTriggerRouter + HookRouter  │
└─────────────────────────┬───────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌─────────┐         ┌─────────┐         ┌─────────┐
│ Claude  │         │ Ollama  │         │ Codex   │
│ Code    │         │ (FREE)  │         │ (API)   │
│ (CLI)   │         │         │         │         │
└────┬────┘         └────┬────┘         └────┬────┘
     │                   │                   │
     ▼                   ▼                   ▼
┌─────────┐         ┌─────────┐         ┌─────────┐
│복잡한 작업│         │디버깅    │         │코드 생성 │
│설계 결정 │         │테스트    │         │리팩터링  │
│리뷰      │         │린트      │         │          │
└─────────┘         └─────────┘         └─────────┘
```

---

## 플랫폼별 역할

| 플랫폼 | 비용 티어 | 주요 역할 | 트리거 키워드 |
|--------|----------|----------|--------------|
| **Claude Code** | EXPENSIVE | 복잡한 설계, 아키텍처 결정, 리뷰 | `design`, `architect`, `complex`, `review` |
| **Ollama** | FREE | 디버깅, 테스트, 린트, 타입체크 | `debug`, `test`, `lint`, `fix`, `type` |
| **Codex** | CHEAP | 코드 생성, 리팩터링, 구현 | `implement`, `refactor`, `generate`, `code` |
| **OpenCode** | CHEAP | 빠른 탐색, 검색, 분석 | `search`, `find`, `explore`, `analyze` |

---

## 라우팅 규칙

### 규칙 1: FREE 우선 (100% 절감)

```yaml
condition:
  task_type:
    - debug
    - test
    - lint
    - type_check
    - simple_fix
action: route_to_ollama
executor: 오호대장군
cost: $0.00
```

### 규칙 2: CHEAP 차선 (98% 절감)

```yaml
condition:
  task_type:
    - implement
    - refactor
    - generate
  complexity: "<= 5"
action: route_to_codex
cost: $0.00025/1k tokens
```

### 규칙 3: EXPENSIVE 필요시만

```yaml
condition:
  task_type:
    - architect
    - design
    - complex_review
  OR:
    complexity: "> 7"
    risk_score: "> 50"
action: route_to_claude
cost: $0.015/1k tokens
```

---

## 오호대장군 배치 (Ollama)

| 장군 | 모델 | 역할 | 트리거 |
|------|------|------|--------|
| **관우** | qwen2.5-coder:7b | 코드 리뷰 | `review`, `refactor` |
| **장비** | deepseek-r1:7b | 버그 추적 | `debug`, `bug`, `error` |
| **조운** | qwen3:8b | 테스트 생성 | `test`, `pytest`, `coverage` |
| **마초** | codestral:latest | 빠른 생성 | `implement`, `generate` |
| **황충** | qwen3-vl:latest | UI 분석 | `ui`, `screenshot`, `visual` |

---

## 출력 형식

```yaml
multiplatform_routing:
  task: "$ARGUMENTS"
  philosophy: "세종대왕의 정신"

  analysis:
    keywords_detected:
      - "[키워드1]"
      - "[키워드2]"
    complexity_score: [0-10]
    risk_score: [0-100]

  routing_decision:
    primary_platform: "[Claude/Ollama/Codex/OpenCode]"
    cost_tier: [FREE/CHEAP/EXPENSIVE]
    executor: "[실행자]"

  cost_estimate:
    estimated_tokens: [토큰 수]
    estimated_cost: "$[비용]"
    savings_vs_opus: "[절감률]%"

  parallel_possible: [true/false]
  fallback_platform: "[대체 플랫폼]"

  recommendation: "[권고사항]"
```

---

## 토큰 버닝 최적화

```yaml
optimization_strategies:
  # 전략 1: FREE 티어 최대 활용
  free_first:
    description: "디버깅/테스트는 항상 Ollama"
    savings: "100%"

  # 전략 2: 병렬 분산
  parallel_distribution:
    description: "독립 작업을 오호대장군에게 분배"
    savings: "60-80%"

  # 전략 3: 캐시 활용
  cache_hit:
    description: "유사 작업 결과 재사용"
    savings: "100%"

  # 전략 4: 복잡도 기반
  complexity_based:
    description: "복잡도 낮으면 CHEAP 티어"
    savings: "98%"

expected_total_savings: "50-70%"
```

---

## 사용 예시

### 예시 1: 디버깅 (FREE)

```bash
/multiplatform "pytest 실패 수정"

# 라우팅 결과:
# platform: Ollama
# executor: 조운 (趙雲)
# cost: $0.00
```

### 예시 2: 코드 생성 (CHEAP)

```bash
/multiplatform "새로운 API 엔드포인트 구현"

# 라우팅 결과:
# platform: Codex
# cost_tier: CHEAP
# cost: ~$0.05
```

### 예시 3: 아키텍처 설계 (EXPENSIVE)

```bash
/multiplatform "마이크로서비스 아키텍처 설계"

# 라우팅 결과:
# platform: Claude Code
# cost_tier: EXPENSIVE
# reason: "복잡한 설계 작업"
```

---

## 세종대왕의 정신

### 장영실 (眞) - 정확한 라우팅

> "측우기처럼 정확하게 작업을 분류한다"

### 이순신 (善) - 안전한 실행

> "위험 작업은 항상 신중하게 처리한다"

### 신사임당 (美) - 최적의 UX

> "사용자에게 최적의 비용과 속도를 제공한다"

---

## 관련 파일

- Chancellor V3: `packages/afo-core/api/chancellor_v2/orchestrator/`
- CostAwareRouter: `packages/afo-core/api/chancellor_v2/orchestrator/cost_aware_router.py`
- KeyTriggerRouter: `packages/afo-core/api/chancellor_v2/orchestrator/key_trigger_router.py`
- 오호대장군: `.claude/agents/ollama-debugger.md`
