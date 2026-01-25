# HyoDo (孝道) - AFO Kingdom Plugin v3.0.0-ultrawork

> **세종대왕의 정신 + 오호대장군: 전략가가 지휘하고, 무장이 실행한다**

Philosophy-driven agent orchestration plugin for Claude Code, based on the wisdom of **眞善美孝永** (Truth, Goodness, Beauty, Serenity, Eternity).

## What's New in v3.0.0-ultrawork

- **오호대장군 (五虎大將軍)** - Ollama 기반 FREE 티어 디버깅 군단
- **훅 시스템** - pre_tool, on_error 훅으로 자동화
- **ultrawork** - 병렬 작업 실행 (비용 $0.00)
- **토큰 버닝 최적화** - 50-70% 비용 절감

### v2.0.0-sejong (이전)

- **세종대왕의 정신** - 삼국지 전략가에서 조선 위인으로 마이그레이션
- **Chancellor V3** - CostAwareRouter + KeyTriggerRouter 연동
- **十一臟腑** - 11 Organs 헬스체크 시스템
- **비용 최적화** - 40% 비용 절감 라우팅

## Installation

```bash
/plugin install hyodo@claude-plugin-directory
```

Or clone directly:
```bash
git clone https://github.com/lofibrainwav/HyoDo.git
```

## The 5 Pillars (五柱)

| Pillar | Korean | Weight | Meaning |
|--------|--------|--------|---------|
| **眞** (Truth) | 진 | 35% | Technical accuracy, verifiability |
| **善** (Goodness) | 선 | 35% | Ethical soundness, stability |
| **美** (Beauty) | 미 | 20% | Elegant design, UX clarity |
| **孝** (Serenity) | 효 | 8% | Frictionless operation |
| **永** (Eternity) | 영 | 2% | Long-term sustainability |

## Trinity Score Formula

```
Trinity Score = (眞 × 0.35) + (善 × 0.35) + (美 × 0.20) + (孝 × 0.08) + (永 × 0.02)
```

## Commands

| Command | Description |
|---------|-------------|
| `/trinity [task]` | Calculate Trinity Score |
| `/strategist [topic]` | 세종대왕의 정신 - 3 전략가 분석 |
| `/ultrawork [tasks]` | **NEW** 병렬 작업 실행 - 오호대장군 |
| `/chancellor-v3` | Chancellor V3 라우팅 시스템 제어 |
| `/organs` | 十一臟腑 건강 상태 체크 |
| `/cost-estimate` | 작업 비용 사전 예측 |
| `/routing` | KeyTriggerRouter 분석 |
| `/check` | Run 4-Gate CI Protocol |
| `/preflight` | Pre-commit validation |
| `/evidence` | Record decision evidence |
| `/rollback` | Safe rollback procedures |
| `/ssot` | Single Source of Truth |

## 세종대왕의 정신 - The 3 Strategists

| Strategist | Korean | Role | Specialty |
|------------|--------|------|-----------|
| **장영실** | 蔣英實 | 眞 Sword ⚔️ | 측우기의 정밀함 - 기술적 정확성, 검증, 아키텍처 |
| **이순신** | 李舜臣 | 善 Shield 🛡️ | 거북선의 수호 - 안전성, 리스크 평가, 게이트키핑 |
| **신사임당** | 申師任堂 | 美 Bridge 🌉 | 초충도의 예술 - UX, 가독성, 커뮤니케이션 |

### Migration from v1.x

```
Before (삼국지)              After (세종대왕)
─────────────────────────────────────────
제갈량 (諸葛亮)    →    장영실 (蔣英實)    眞
사마의 (司馬懿)    →    이순신 (李舜臣)    善
주유   (周瑜)      →    신사임당 (申師任堂) 美
```

## Agents

| Agent | Purpose |
|-------|---------|
| **trinity-guardian** | Monitors Trinity Score on code changes |
| **quality-gate** | Runs 4-Gate CI (Pyright → Ruff → pytest → SBOM) |
| **ollama-debugger** | **NEW** 오호대장군 - FREE 티어 디버깅 |

## 오호대장군 (五虎大將軍) - Ollama 디버깅 군단

> "전략가가 지휘하고, 무장이 실행한다"

| 장군 | 한자 | 모델 | 역할 |
|------|------|------|------|
| **관우** | 關羽 | qwen2.5-coder:7b | 코드 리뷰/리팩터링 |
| **장비** | 張飛 | deepseek-r1:7b | 버그 추적/디버깅 |
| **조운** | 趙雲 | qwen3:8b | 테스트 생성/검증 |
| **마초** | 馬超 | codestral:latest | 빠른 코드 생성 |
| **황충** | 黃忠 | qwen3-vl:latest | UI/스크린샷 분석 |

**비용**: $0.00 (모든 작업 FREE 티어)

## Hooks

| Hook | Type | Description |
|------|------|-------------|
| **cost_check** | pre_tool | 비용 티어 체크 - FREE 우선 라우팅 |
| **safety_gate** | pre_tool | 이순신 안전 게이트 - 위험 작업 차단 |
| **ollama_debug** | on_error | 에러 시 오호대장군 자동 호출 |

## Skills

| Skill | Trigger |
|-------|---------|
| **trinity-score-calculator** | Trinity Score calculation requests |
| **strategy-engine** | Strategic decision making |
| **philosophy-guide** | Philosophy and ethics questions |
| **kingdom-navigator** | Codebase navigation |

## Decision Thresholds

| Condition | Action |
|-----------|--------|
| Score >= 90 AND Risk <= 10 | **AUTO_RUN** |
| Score 70-89 OR Risk 11-30 | **ASK_COMMANDER** |
| Score < 70 OR Risk > 30 | **BLOCK** |

## Plugin Structure

```
HyoDo/
├── .claude-plugin/
│   └── plugin.json        # Plugin metadata (v3.0.0-ultrawork)
├── commands/              # 12 slash commands
│   ├── trinity.md
│   ├── strategist.md      # 세종대왕의 정신
│   ├── ultrawork.md       # NEW: 병렬 실행
│   ├── chancellor-v3.md   # V3 라우팅
│   ├── organs.md          # 十一臟腑
│   ├── cost-estimate.md   # 비용 예측
│   ├── routing.md         # 트리거 분석
│   ├── check.md
│   ├── preflight.md
│   ├── evidence.md
│   ├── rollback.md
│   └── ssot.md
├── agents/                # 3 autonomous agents
│   ├── trinity-guardian.md
│   ├── quality-gate.md
│   └── ollama-debugger.md # NEW: 오호대장군
├── hooks/                 # NEW: Hook system
│   ├── pre_tool/
│   │   ├── cost_check.md
│   │   └── safety_gate.md
│   └── on_error/
│       └── ollama_debug.md
├── skills/                # 4 skill modules
│   ├── trinity-score-calculator/
│   ├── strategy-engine/
│   ├── philosophy-guide/
│   └── kingdom-navigator/
├── README.md
├── QUICK_START.md         # NEW: 5분 시작 가이드
├── CONTRIBUTING.md        # NEW: 기여 가이드
├── CHANGELOG.md           # NEW: 변경 이력
├── SECURITY.md            # NEW: 보안 정책
└── LICENSE                # MIT License
```

## Quick Start

```bash
# Calculate Trinity Score
/trinity "implement new feature"

# Get Strategist perspectives (세종대왕의 정신)
/strategist "architectural decision"

# Check cost tier
/cost-estimate "deploy to production"

# Run quality gates
/check
```

## Philosophy

**HyoDo (孝道)** means "The Way of Serenity" - now enhanced with **세종대왕의 정신** (Spirit of King Sejong).

The name reflects the core belief that sustainable software comes from:
- **Serenity (孝)**: Frictionless, peaceful user experience
- **Eternity (永)**: Long-term thinking and maintainability
- **세종대왕의 정신**: 백성을 위한 실용적 혁신과 문화적 융성

## Origin

This plugin is derived from the [AFO Kingdom](https://github.com/anthropics/AFO_Kingdom) project, an agent orchestration system built on East Asian philosophy principles.

## Documentation

| Document | Description |
|----------|-------------|
| [QUICK_START.md](QUICK_START.md) | 5분 시작 가이드 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 기여 가이드 (眞善美 원칙) |
| [CHANGELOG.md](CHANGELOG.md) | 버전별 변경 이력 |
| [SECURITY.md](SECURITY.md) | 이순신 보안 정책 |

## License

MIT - See [LICENSE](LICENSE) for details

---

*"세종대왕의 정신: 장영실의 정밀함, 이순신의 수호, 신사임당의 예술"*
