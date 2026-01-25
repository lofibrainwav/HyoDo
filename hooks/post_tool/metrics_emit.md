---
hook_type: post_tool
name: "metrics_emit"
displayName: "메트릭 수집 훅"
description: "도구 실행 후 성능 및 비용 메트릭 수집"
priority: 70
enabled: true
---

# 메트릭 수집 훅 (Metrics Emit Hook)

> "이순신의 학익진처럼 전체 전장을 파악한다"

도구 실행 후 성능, 비용, 품질 메트릭을 수집하여 十一臟腑 시스템에 전달합니다.

---

## 훅 정보

| 항목 | 값 |
|------|-----|
| **훅 타입** | post_tool |
| **우선순위** | 70 |
| **활성화** | true |

---

## 수집 메트릭

### 성능 메트릭

```yaml
performance_metrics:
  execution_time_ms: [실행 시간]
  tokens_used:
    input: [입력 토큰]
    output: [출력 토큰]
    total: [총 토큰]
  memory_mb: [메모리 사용량]
  cpu_percent: [CPU 사용률]
```

### 비용 메트릭

```yaml
cost_metrics:
  tier: [FREE/CHEAP/EXPENSIVE]
  model: "[사용 모델]"
  estimated_cost: "$[비용]"
  actual_cost: "$[실제 비용]"
  savings_vs_opus: "[절감률]%"
```

### 품질 메트릭

```yaml
quality_metrics:
  trinity_score: [0-100]
  pillars:
    truth: [0-100]
    goodness: [0-100]
    beauty: [0-100]
    serenity: [0-100]
    eternity: [0-100]
```

### 오호대장군 메트릭

```yaml
generals_metrics:
  total_deployments: [배치 수]
  generals:
    guan_yu:     # 관우
      tasks: [작업 수]
      success_rate: [성공률]%
    zhang_fei:   # 장비
      tasks: [작업 수]
      success_rate: [성공률]%
    zhao_yun:    # 조운
      tasks: [작업 수]
      success_rate: [성공률]%
    ma_chao:     # 마초
      tasks: [작업 수]
      success_rate: [성공률]%
    huang_zhong: # 황충
      tasks: [작업 수]
      success_rate: [성공률]%
  parallel_executions: [병렬 실행 수]
  total_cost: "$0.00"
```

---

## 十一臟腑 연동

```yaml
organs_integration:
  心_Redis:        # 세션 메트릭 캐시
    action: "cache_metrics"
  肝_PostgreSQL:   # 장기 메트릭 저장
    action: "persist_metrics"
  腦_Soul_Engine:  # 분석 트리거
    action: "analyze_trends"
  耳_Observability: # 실시간 모니터링
    action: "emit_to_dashboard"
```

---

## 출력 형식

```yaml
metrics_emit_result:
  hook: "metrics_emit"
  status: [emitted/skipped]

  metrics:
    performance:
      execution_time_ms: [시간]
      tokens_total: [토큰]
    cost:
      tier: "[티어]"
      estimated: "$[비용]"
      saved: "$[절감]"
    quality:
      trinity_score: [점수]

  organs_notified:
    - 心_Redis
    - 耳_Observability

  message: "[메트릭 메시지]"
```

---

## 집계 대시보드

### 일일 요약

```yaml
daily_summary:
  date: "2026-01-24"

  totals:
    tool_executions: [총 실행]
    tokens_used: [총 토큰]
    estimated_cost: "$[총 비용]"

  cost_breakdown:
    FREE: [횟수] ($0.00)
    CHEAP: [횟수] ($[비용])
    EXPENSIVE: [횟수] ($[비용])

  savings:
    vs_all_opus: "$[절감액]"
    percentage: "[절감률]%"

  generals_performance:
    most_active: "[장군명]"
    highest_success: "[장군명]"
    parallel_efficiency: "[효율]%"
```

---

## 예시

### 메트릭 수집 결과

```yaml
metrics_emit_result:
  status: emitted

  metrics:
    performance:
      execution_time_ms: 1234
      tokens_total: 5000
    cost:
      tier: "FREE"
      estimated: "$0.00"
      saved: "$0.075"
    quality:
      trinity_score: 85

  organs_notified:
    - 心_Redis
    - 耳_Observability

  message: "오호대장군 조운 테스트 실행 메트릭 수집 완료"
```

---

## 세종대왕의 정신

### 이순신 (善) - 학익진의 전장 파악

> "전장 전체를 파악해야 승리할 수 있다"

- 전체 시스템 상태 모니터링
- 이상 징후 조기 감지
- 최적화 기회 식별

---

## 관련 파일

- 十一臟腑: `.claude/commands/organs.md`
- 건강 체크: `.claude/commands/health.md`
- 대시보드: `packages/afo-core/api/dashboard/`
