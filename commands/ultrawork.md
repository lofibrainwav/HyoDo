---
description: "병렬 작업 실행 - 오호대장군 + Chancellor V3"
allowed-tools: Read, Grep, Glob, Bash(pytest:*), Bash(ruff:*), Bash(pyright:*), Task
impact: HIGH
tags: [ultrawork, parallel, orchestration, multi-agent]
triggers: [ultrawork, parallel, 동시에, 병렬로]
---

# /ultrawork - 병렬 작업 실행

> "세종대왕이 지휘하고, 오호대장군이 동시에 진격한다"

$ARGUMENTS 를 분석하여 여러 작업을 병렬로 실행합니다. 오호대장군(Ollama)을 활용하여 비용 $0.00으로 최대 효율을 달성합니다.

---

## 트리거 키워드

| 키워드 | 한국어 | 예시 |
|--------|--------|------|
| `ultrawork` | - | `/ultrawork "fix all errors"` |
| `parallel` | - | `parallel fix tests and lint` |
| `동시에` | 同時에 | `테스트와 린트 동시에 수정해` |
| `병렬로` | 並列로 | `병렬로 타입체크하고 빌드해` |

---

## 오케스트레이션 아키텍처

```
┌─────────────────────────────────────────────────────┐
│           /ultrawork 명령어 파서                      │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│           Chancellor V3 (작업 분배기)                 │
│                                                     │
│  1. 작업 분해 (장영실) - 眞 Sword                     │
│  2. 안전 검토 (이순신) - 善 Shield                    │
│  3. UX 최적화 (신사임당) - 美 Bridge                  │
└─────────────────────────┬───────────────────────────┘
                          │
    ┌─────────┬───────────┼───────────┬─────────┐
    │         │           │           │         │
    ▼         ▼           ▼           ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│ 관우  │ │ 장비  │ │ 조운  │ │ 마초  │ │ 황충  │
│ 코드  │ │ 디버깅│ │ 테스트│ │ 생성  │ │ UI   │
│ 리뷰  │ │       │ │       │ │       │ │ 분석  │
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
    │         │         │         │         │
    └─────────┴─────────┴─────────┴─────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│           결과 통합 (신사임당)                        │
└─────────────────────────────────────────────────────┘
```

---

## 작업 분해 규칙

### 자동 분해 패턴

| 패턴 | 분해 방식 | 병렬 가능 |
|------|----------|----------|
| `A and B` | [A], [B] | O |
| `A, B, C` | [A], [B], [C] | O |
| `A then B` | [A] → [B] | X (순차) |
| `A with B` | [A + B] | 조건부 |

### 예시

```yaml
input: "테스트 수정하고 린트 고치고 타입 체크해"

decomposition:
  - task_1: "테스트 수정"
    executor: 조운 (趙雲)
    model: qwen3:8b
    parallel: true

  - task_2: "린트 수정"
    executor: 마초 (馬超)
    model: codestral:latest
    parallel: true

  - task_3: "타입 체크"
    executor: 관우 (關羽)
    model: qwen2.5-coder:7b
    parallel: true
```

---

## 실행 워크플로우

### Phase 1: 작업 분해 (장영실)

```yaml
step: decompose
strategist: 장영실 (眞 Sword)
actions:
  - 명령어 파싱
  - 독립 작업 식별
  - 의존성 분석
  - 병렬 가능 여부 판단
```

### Phase 2: 안전 검토 (이순신)

```yaml
step: safety_check
strategist: 이순신 (善 Shield)
actions:
  - 위험 키워드 검사
  - 충돌 가능성 확인
  - 롤백 계획 수립
```

### Phase 3: 병렬 실행 (오호대장군)

```yaml
step: parallel_execute
executors:
  - 관우: 코드 리뷰 작업
  - 장비: 디버깅 작업
  - 조운: 테스트 작업
  - 마초: 코드 생성 작업
  - 황충: UI 분석 작업
cost_tier: FREE
```

### Phase 4: 결과 통합 (신사임당)

```yaml
step: integrate_results
strategist: 신사임당 (美 Bridge)
actions:
  - 결과 취합
  - 충돌 해결
  - 가독성 있는 리포트 생성
```

---

## 출력 형식

```yaml
ultrawork_result:
  command: "$ARGUMENTS"
  philosophy: "세종대왕의 정신 + 오호대장군"

  decomposition:
    total_tasks: [작업 수]
    parallel_tasks: [병렬 작업 수]
    sequential_tasks: [순차 작업 수]
    tasks:
      - name: "[작업명]"
        executor: "[장군명]"
        status: [pending/running/completed/failed]

  execution:
    mode: "parallel"
    total_executors: [사용 장군 수]
    cost_tier: FREE
    estimated_cost: "$0.00"

  results:
    - task: "[작업1]"
      executor: "[장군명]"
      status: [success/failure]
      output: "[결과]"

  integration:
    strategist: "신사임당 (申師任堂)"
    conflicts_resolved: [충돌 수]
    final_status: [SUCCESS/PARTIAL/FAILED]

  summary:
    tasks_completed: [완료 수]/[전체]
    time_saved: "[절약 시간]%"
    cost_saved: "$[절약 비용]"

  next_steps:
    - "[다음 단계 1]"
    - "[다음 단계 2]"
```

---

## 사용 예시

### 예시 1: 전체 품질 검사

```bash
/ultrawork "테스트 실행하고 린트 체크하고 타입 검사해"

# 실행 결과:
# ├─ 조운 (qwen3:8b) → pytest 실행
# ├─ 마초 (codestral) → ruff 검사
# └─ 관우 (qwen2.5-coder) → pyright 검사
#
# 총 비용: $0.00
# 시간 절약: 66% (병렬 실행)
```

### 예시 2: 에러 일괄 수정

```bash
/ultrawork "lint 에러 5개 수정하고 테스트 다시 실행"

# 실행 결과:
# ├─ 마초 × 5 (병렬) → 각 lint 에러 수정
# └─ 조운 (순차) → 최종 테스트
#
# 총 비용: $0.00
```

### 예시 3: 코드 리뷰 + 테스트

```bash
/ultrawork "PR 코드 리뷰하고 동시에 테스트 커버리지 확인"

# 실행 결과:
# ├─ 관우 → 코드 리뷰
# └─ 조운 → 커버리지 분석
#
# 총 비용: $0.00
```

---

## 비용 최적화

```
Traditional (순차, Claude):
────────────────────────────────
3 작업 × opus ($0.015/1k) × 5k 토큰 × 순차
= $0.225 + 3x 시간

Ultrawork (병렬, Ollama):
────────────────────────────────
3 작업 × FREE ($0.00) × 5k 토큰 × 병렬
= $0.00 + 1x 시간

비용 절감: 100%
시간 절감: 66%
```

---

## 세종대왕의 정신

### 장영실 (眞) - 작업 분해

> "측우기처럼 정밀하게 작업을 분해한다"

### 이순신 (善) - 안전 검토

> "거북선처럼 안전하게 병렬 실행을 보호한다"

### 신사임당 (美) - 결과 통합

> "초충도처럼 아름답게 결과를 통합한다"

---

## 제한사항

1. **위험 작업 병렬 금지**: `delete`, `production`, `deploy` 포함 시 순차 실행
2. **최대 병렬 수**: 5개 (오호대장군 수)
3. **의존성 있는 작업**: 자동으로 순차 실행

---

## 관련 파일

- Chancellor V3: `packages/afo-core/api/chancellor_v2/orchestrator/`
- 오호대장군: `.claude/agents/ollama-debugger.md`
- 비용 라우터: `packages/afo-core/api/chancellor_v2/orchestrator/cost_aware_router.py`
