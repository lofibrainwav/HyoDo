---
description: "작업 비용 사전 예측 (CostAwareRouter)"
allowed-tools: Read, Bash(curl:*)
impact: LOW
tags: [cost, optimization, routing, estimate]
---

# 작업 비용 사전 예측

$ARGUMENTS 작업의 예상 비용을 CostAwareRouter로 분석합니다.

## 비용 티어

```yaml
cost_tiers:
  FREE:
    model: qwen3:8b (Ollama)
    provider: ollama
    cost_per_1k_tokens: $0.000
    quality_score: 0.70
    max_tokens: 8192
    best_for:
      - 단순 조회 (read, list, show)
      - 도움말 요청 (help, explain)
      - 검색 (search, find)

  CHEAP:
    model: claude-haiku-4-5-20251001
    provider: anthropic
    cost_per_1k_tokens: $0.00025
    quality_score: 0.85
    max_tokens: 4096
    best_for:
      - 일반 구현 (implement, create, add)
      - 디버깅 (debug, fix)
      - 테스트 작성 (test)
      - 업데이트 (update, modify)

  EXPENSIVE:
    model: claude-opus-4-5-20251101
    provider: anthropic
    cost_per_1k_tokens: $0.015
    quality_score: 0.98
    max_tokens: 8192
    best_for:
      - 프로덕션 배포 (production, deploy)
      - 보안 관련 (auth, secret, password)
      - 아키텍처 결정 (refactor, architect)
      - 삭제 작업 (delete, drop, destroy)
      - 마이그레이션 (migration)
```

---

## 복잡도 점수 계산

### 고복잡도 키워드 (+3점)

- `production`, `deploy`, `delete`, `drop`
- `auth`, `secret`, `password`, `credential`
- `migration`, `refactor`, `architect`

### 중복잡도 키워드 (+1점)

- `implement`, `create`, `add`, `update`
- `modify`, `test`, `debug`, `fix`

### 저복잡도 키워드 (-1점)

- `read`, `list`, `show`, `explain`
- `search`, `find`, `help`, `docs`

### 추가 요소

- 명령어 길이 > 500자: +3점
- 명령어 길이 > 200자: +2점
- 명령어 길이 > 100자: +1점
- Plan steps > 5: +2점
- Plan steps > 3: +1점
- `requires_approval`: +2점
- `dry_run`: -1점

### 티어 결정

- 점수 >= 5: **EXPENSIVE**
- 점수 >= 2: **CHEAP**
- 점수 < 2: **FREE**

---

## 출력 형식

```yaml
cost_estimate:
  command: "$ARGUMENTS"
  analysis:
    complexity_score: [점수]
    matched_keywords:
      high: [고복잡도 키워드들]
      medium: [중복잡도 키워드들]
      low: [저복잡도 키워드들]

  recommendation:
    tier: [FREE | CHEAP | EXPENSIVE]
    model: [모델명]
    provider: [ollama | anthropic]
    quality_score: [0.70 | 0.85 | 0.98]

  cost_projection:
    estimated_tokens: [예상 토큰 수]
    cost_per_1k: $[비용]
    total_estimated: $[총 예상 비용]

  strategist_note:
    jang_yeong_sil: "[기술적 복잡도 평가]"
    yi_sun_sin: "[리스크 평가]"
    shin_saimdang: "[사용자 경험 평가]"
```

---

## 사용 예시

```bash
# 단순 조회 → FREE
/cost-estimate "list all files in src directory"
# 결과: FREE, qwen3:8b, $0.00

# 일반 구현 → CHEAP
/cost-estimate "implement a new utility function for date formatting"
# 결과: CHEAP, claude-haiku-4-5, ~$0.0005

# 프로덕션 배포 → EXPENSIVE
/cost-estimate "deploy authentication module to production"
# 결과: EXPENSIVE, claude-opus-4-5, ~$0.03
```

---

## 세종대왕의 정신과 비용 최적화

### 善 (Goodness) - 이순신의 관점 🛡️

> "백성의 부담을 최소화하라"

비용 최적화는 善의 원칙입니다:
- 불필요한 고비용 모델 사용 방지
- 작업에 적합한 모델 선택
- 40% 비용 절감 목표

---

## 관련 파일

- `packages/afo-core/api/chancellor_v2/orchestrator/cost_aware_router.py`
