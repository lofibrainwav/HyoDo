---
description: "Chancellor V3 라우팅 시스템 제어 및 분석"
allowed-tools: Read, Glob, Grep, Bash(curl:*)
impact: MEDIUM
tags: [chancellor, routing, cost, optimization, v3]
---

# Chancellor V3 라우팅 시스템

Chancellor V3의 지능형 라우팅 시스템을 분석하고 제어합니다.

## 핵심 컴포넌트

### 1. CostAwareRouter (비용 인식 라우터)

작업 복잡도에 따라 최적의 모델을 자동 선택합니다.

```yaml
cost_tiers:
  FREE:
    model: qwen3:8b (Ollama)
    cost: $0.000/1k tokens
    quality: 0.70
    use_case: 단순 조회, 도움말, 검색

  CHEAP:
    model: claude-haiku-4-5
    cost: $0.00025/1k tokens
    quality: 0.85
    use_case: 일반 구현, 디버깅, 테스트

  EXPENSIVE:
    model: claude-opus-4-5
    cost: $0.015/1k tokens
    quality: 0.98
    use_case: 프로덕션, 보안, 아키텍처
```

### 2. KeyTriggerRouter (키워드 트리거 라우터)

명령어 키워드를 분석하여 필요한 전략가(Pillar)만 선택합니다.

#### 眞 (Truth) 트리거 - 장영실 ⚔️

- `type-check`, `lint`, `test`, `build`
- `implement`, `api`, `schema`, `algorithm`
- `refactor`, `optimize`, `performance`

#### 善 (Goodness) 트리거 - 이순신 🛡️

- `delete`, `drop`, `remove`, `destroy`
- `secret`, `password`, `credential`, `token`
- `auth`, `production`, `deploy`, `migration`
- `--force`, `--hard`, `rm -rf`

#### 美 (Beauty) 트리거 - 신사임당 🌉

- `ui`, `ux`, `design`, `style`, `css`
- `format`, `readme`, `docs`, `comment`
- `explain`, `simplify`, `clean`, `readable`

---

## 사용법

### 비용 티어 분석

$ARGUMENTS 명령어의 예상 비용 티어를 분석합니다:

```bash
# 분석 요청
/chancellor-v3 cost "deploy to production"
# 결과: EXPENSIVE (production 키워드 감지)

/chancellor-v3 cost "list all files"
# 결과: FREE (read, list 키워드 감지)
```

### 키워드 트리거 분석

```bash
/chancellor-v3 triggers "implement new API endpoint with auth"
# 결과:
#   眞 (장영실): implement, api
#   善 (이순신): auth
#   美 (신사임당): -
#   선택된 Pillars: [truth, goodness]
```

### 라우팅 결정 조회

```bash
/chancellor-v3 routing "refactor authentication module"
# 결과:
#   Cost Tier: EXPENSIVE (auth + refactor)
#   Pillars: [truth, goodness]
#   Model: claude-opus-4-5
#   Estimated Cost: $0.03 (2k tokens 기준)
```

---

## 출력 형식

```yaml
chancellor_v3_analysis:
  command: "$ARGUMENTS"

  cost_router:
    complexity_score: [점수]
    tier: [FREE | CHEAP | EXPENSIVE]
    model: [모델명]
    estimated_cost_usd: [비용]

  key_trigger_router:
    matched_triggers:
      truth: [매칭된 키워드들]
      goodness: [매칭된 키워드들]
      beauty: [매칭된 키워드들]
    scores:
      truth: [점수]
      goodness: [점수]
      beauty: [점수]
    selected_pillars: [선택된 기둥들]
    confidence: [신뢰도]

  strategists:
    jang_yeong_sil: [활성화 여부]  # 眞
    yi_sun_sin: [활성화 여부]      # 善
    shin_saimdang: [활성화 여부]   # 美

  recommendation: "[라우팅 권고사항]"
```

---

## 세종대왕의 정신과 V3

Chancellor V3는 세종대왕의 정신을 계승합니다:

```
┌────────────────────────────────────────────────────────┐
│                    Chancellor V3                        │
│            "효율적이고 지혜로운 통치"                    │
├────────────────────────────────────────────────────────┤
│                                                        │
│  CostAwareRouter          KeyTriggerRouter             │
│  (비용 최적화)             (지능형 선택)                │
│       ↓                         ↓                      │
│  ┌─────────┐              ┌──────────────┐            │
│  │ FREE    │              │ 眞 장영실    │            │
│  │ CHEAP   │      →       │ 善 이순신    │            │
│  │ EXPENSIVE│              │ 美 신사임당  │            │
│  └─────────┘              └──────────────┘            │
│                                                        │
│  비용 인식 라우팅         반복 평가 감소               │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 관련 파일

- `packages/afo-core/api/chancellor_v2/orchestrator/cost_aware_router.py`
- `packages/afo-core/api/chancellor_v2/orchestrator/key_trigger_router.py`
- `packages/afo-core/api/chancellor_v2/orchestrator/chancellor_orchestrator.py`
