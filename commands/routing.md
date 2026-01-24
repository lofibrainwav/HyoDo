---
description: "KeyTriggerRouter 분석 - 眞善美 트리거 매칭"
allowed-tools: Read, Bash(curl:*)
impact: LOW
tags: [routing, triggers, pillars, optimization]
---

# KeyTriggerRouter 분석

$ARGUMENTS 명령어의 키워드 트리거를 분석하여 필요한 전략가(Pillar)를 선택합니다.

## 트리거 매칭 시스템

KeyTriggerRouter는 명령어에서 키워드를 분석하여 필요한 전략가만 활성화합니다.
불필요한 LLM 호출을 **30-50% 감소**시킵니다.

---

## 眞 (Truth) 트리거 - 장영실 ⚔️

> "측우기의 정밀함으로 기술적 정확성 검증"

| 트리거 | 가중치 | 설명 |
|--------|--------|------|
| `type-check` | 1.5 | 타입 체크 |
| `lint(ing)?` | 1.3 | 린트 |
| `test(s\|ing)?` | 1.5 | 테스트 |
| `build` | 1.2 | 빌드 |
| `implement` | 1.5 | 구현 |
| `code` | 1.0 | 코드 |
| `function` | 1.2 | 함수 |
| `class` | 1.2 | 클래스 |
| `api` | 1.3 | API |
| `endpoint` | 1.3 | 엔드포인트 |
| `schema` | 1.4 | 스키마 |
| `model` | 1.2 | 모델 |
| `algorithm` | 1.5 | 알고리즘 |
| `debug` | 1.3 | 디버그 |
| `fix bug/error` | 1.4 | 버그 수정 |
| `refactor` | 1.5 | 리팩터링 |
| `optimize` | 1.4 | 최적화 |
| `performance` | 1.3 | 성능 |

---

## 善 (Goodness) 트리거 - 이순신 🛡️

> "거북선의 수호로 시스템 안전성 보장"

| 트리거 | 가중치 | 설명 |
|--------|--------|------|
| `delete` | 2.0 | 삭제 |
| `drop` | 2.0 | 드롭 |
| `remove` | 1.5 | 제거 |
| `destroy` | 2.0 | 파괴 |
| `secret` | 2.0 | 시크릿 |
| `password` | 2.0 | 패스워드 |
| `credential` | 2.0 | 자격증명 |
| `token` | 1.8 | 토큰 |
| `auth(entication)?` | 1.8 | 인증/인가 |
| `permission` | 1.7 | 권한 |
| `prod(uction)?` | 2.0 | 프로덕션 |
| `deploy` | 1.8 | 배포 |
| `migration` | 1.8 | 마이그레이션 |
| `backup` | 1.5 | 백업 |
| `restore` | 1.5 | 복원 |
| `security` | 1.8 | 보안 |
| `privacy` | 1.7 | 프라이버시 |
| `sensitive` | 1.6 | 민감 |
| `encrypt` | 1.5 | 암호화 |
| `--force` | 2.0 | 강제 플래그 |
| `--hard` | 2.0 | 하드 플래그 |
| `rm -rf` | 2.5 | rm -rf 명령 |

---

## 美 (Beauty) 트리거 - 신사임당 🌉

> "초충도의 예술로 UX 우수성 확보"

| 트리거 | 가중치 | 설명 |
|--------|--------|------|
| `ui` | 1.5 | UI |
| `ux` | 1.5 | UX |
| `design` | 1.3 | 디자인 |
| `style` | 1.2 | 스타일 |
| `css` | 1.3 | CSS |
| `tailwind` | 1.3 | Tailwind |
| `format` | 1.2 | 포맷 |
| `readme` | 1.4 | README |
| `doc(s)?` | 1.3 | 문서 |
| `comment` | 1.2 | 주석 |
| `explain` | 1.3 | 설명 |
| `simplif(y\|ication)` | 1.4 | 단순화 |
| `clean` | 1.2 | 정리 |
| `readab(le\|ility)` | 1.4 | 가독성 |
| `user-friendly` | 1.5 | 사용자 친화적 |
| `intuitive` | 1.4 | 직관적 |
| `component` | 1.2 | 컴포넌트 |
| `layout` | 1.3 | 레이아웃 |

---

## Pillar 선택 규칙

1. **점수 > 0인 모든 Pillar 선택**
2. **최소 2개 Pillar 보장** (min_pillars = 2)
3. **아무 매칭 없으면 전체 선택** [truth, goodness, beauty]

---

## 출력 형식

```yaml
routing_analysis:
  command: "$ARGUMENTS"

  trigger_matches:
    truth:
      matched: [매칭된 트리거들]
      score: [점수]
      strategist: "장영실 (蔣英實)"
    goodness:
      matched: [매칭된 트리거들]
      score: [점수]
      strategist: "이순신 (李舜臣)"
    beauty:
      matched: [매칭된 트리거들]
      score: [점수]
      strategist: "신사임당 (申師任堂)"

  selection:
    pillars: [선택된 기둥들]
    priority_order: [점수 순 정렬]
    confidence: [0.0-1.0]
    total_triggers_matched: [총 매칭 수]

  optimization:
    skipped_pillars: [건너뛴 기둥들]
    evaluation_reduction: "[30-50]%"

  recommendation: "[라우팅 권고사항]"
```

---

## 사용 예시

```bash
# 기술적 작업 → 眞 + 善 활성화
/routing "implement new API endpoint with authentication"
# 결과: [truth, goodness] (beauty 건너뜀)

# UI 작업 → 眞 + 美 활성화
/routing "redesign the dashboard layout with better UX"
# 결과: [truth, beauty] (goodness 건너뜀)

# 삭제 작업 → 善 우선 활성화
/routing "delete user data from production database"
# 결과: [goodness, truth] (goodness 최우선)
```

---

## 세종대왕의 정신과 라우팅

### 眞 (Truth) - 장영실의 지혜

> "필요한 것만 정확하게 측정하라"

불필요한 평가를 줄여 효율성을 높입니다.

### 善 (Goodness) - 이순신의 수호

> "위험한 작업에는 반드시 방패를 들어라"

위험 키워드 감지 시 善 전략가를 최우선 활성화합니다.

### 美 (Beauty) - 신사임당의 예술

> "사용자 경험이 중요할 때만 붓을 들어라"

UX 관련 작업에서만 美 전략가를 활성화합니다.

---

## 관련 파일

- `packages/afo-core/api/chancellor_v2/orchestrator/key_trigger_router.py`
