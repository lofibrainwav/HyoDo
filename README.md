# HyoDo (孝道) - AFO Kingdom Plugin v2.0.0-sejong

> **세종대왕의 정신: 백성을 위한 실용적 혁신**

Philosophy-driven agent orchestration plugin for Claude Code, based on the wisdom of **眞善美孝永** (Truth, Goodness, Beauty, Serenity, Eternity).

## What's New in v2.0.0-sejong

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
│   └── plugin.json        # Plugin metadata (v2.0.0-sejong)
├── commands/              # 11 slash commands
│   ├── trinity.md
│   ├── strategist.md      # 세종대왕의 정신
│   ├── chancellor-v3.md   # NEW: V3 라우팅
│   ├── organs.md          # NEW: 十一臟腑
│   ├── cost-estimate.md   # NEW: 비용 예측
│   ├── routing.md         # NEW: 트리거 분석
│   ├── check.md
│   ├── preflight.md
│   ├── evidence.md
│   ├── rollback.md
│   └── ssot.md
├── agents/                # 2 autonomous agents
│   ├── trinity-guardian.md
│   └── quality-gate.md
├── skills/                # 4 skill modules
│   ├── trinity-score-calculator/
│   ├── strategy-engine/
│   ├── philosophy-guide/
│   └── kingdom-navigator/
└── README.md
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

## License

MIT

---

*"세종대왕의 정신: 장영실의 정밀함, 이순신의 수호, 신사임당의 예술"*
