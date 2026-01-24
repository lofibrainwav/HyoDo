# HyoDo (孝道) - AFO Kingdom Plugin

> **Trinity = Serenity + Eternity**

Philosophy-driven agent orchestration plugin for Claude Code, based on the wisdom of **眞善美孝永** (Truth, Goodness, Beauty, Serenity, Eternity).

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
| `/strategist [topic]` | Get 3 Strategists perspective |
| `/check` | Run 4-Gate CI Protocol |
| `/preflight` | Pre-commit validation |
| `/evidence` | Record decision evidence |
| `/rollback` | Safe rollback procedures |
| `/ssot` | Single Source of Truth |

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

## The 3 Strategists (三策士)

| Strategist | Role | Specialty |
|------------|------|-----------|
| **Zhuge Liang** (諸葛亮) | 眞 Sword | Architecture, long-term vision |
| **Sima Yi** (司馬懿) | 善 Shield | Risk assessment, stability |
| **Zhou Yu** (周瑜) | 美 Bridge | UX, communication |

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
│   └── plugin.json        # Plugin metadata
├── commands/              # 7 slash commands
│   ├── trinity.md
│   ├── strategist.md
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

# Get Strategist perspectives
/strategist "architectural decision"

# Run quality gates
/check
```

## Philosophy

**HyoDo (孝道)** means "The Way of Serenity" - the path that combines **孝 (Serenity)** and **永 (Eternity)** to achieve lasting peace through thoughtful, ethical development.

The name reflects the core belief that sustainable software comes from:
- **Serenity (孝)**: Frictionless, peaceful user experience
- **Eternity (永)**: Long-term thinking and maintainability

## Origin

This plugin is derived from the [AFO Kingdom](https://github.com/anthropics/AFO_Kingdom) project, an agent orchestration system built on East Asian philosophy principles.

## License

MIT

---

*"Trinity = Serenity + Eternity"* - The way of peaceful, eternal code.
