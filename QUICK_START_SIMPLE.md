# HyoDo 3-Minute Quick Start

> A fast, inspectable setup path for using HyoDo with Claude Code.

HyoDo is a code-quality workflow kit for Claude Code. Start with the slash commands
for review and safety checks; use the Python package for scoring and CLI utilities.

## 1. Install

### Recommended: clone, inspect, then run

```bash
git clone https://github.com/lofibrainwav/HyoDo.git ~/.hyodo
cd ~/.hyodo

# Optional but recommended for first-time users
sed -n '1,220p' install_interactive.sh

./install_interactive.sh
```

### One-line install for trusted environments

```bash
curl -sSL https://raw.githubusercontent.com/lofibrainwav/HyoDo/main/install_interactive.sh | bash
```

## 2. Configure your API key

```bash
cd ~/.hyodo
cp .env.minimal .env
nano .env
```

Set:

```bash
ANTHROPIC_API_KEY=your_key_here
```

Do not commit `.env` files with real credentials.

## 3. Run with Claude Code

```bash
cd ~/.hyodo && claude
```

Try these first commands:

```text
/start    # onboarding guide
/check    # code quality check
/score    # review score
/safe     # safety-oriented review
```

---

## Core Commands

| Command | Purpose | Example |
|--------|---------|---------|
| `/start` | Onboarding guide | `/start` |
| `/check` | Code quality check | `/check` |
| `/score` | Review score | `/score` |
| `/safe` | Security and risk scan | `/safe` |
| `/cost` | Cost estimate / routing signal | `/cost` |

---

## What is HYOGOOK V5?

HYOGOOK V5 is HyoDo's optional scoring model. It reviews code through six dimensions and uses a geometric mean component so weak areas remain visible instead of being hidden by stronger ones.

| Pillar | Meaning | What it checks |
|------|---------|----------------|
| 仁 | Benevolence | Developer experience, user serenity |
| 眞 | Truth | Technical accuracy, architecture |
| 善 | Goodness | Security, stability, ethics |
| 忠 | Loyalty | Project context, SSOT alignment |
| 美 | Beauty | Readable code, documentation, UX |
| 永 | Eternity | Maintainability and long-term harmony |

```text
F = (T + G + In + B + C) + ⁵√(T × G × In × B × C)
S = ⁵√(T × G × In × B × C)
```

| F Score | S Score | Meaning | Suggested action |
|--------|--------|---------|------------------|
| F ≥ 54 | S ≥ 8 | Strong | Candidate for approval after human review |
| F ≥ 45 | S ≥ 7 | Good | Review recommended |
| F < 45 | - | Needs work | Fix before merge |

Scores support review. They do not replace human judgment, tests, or security checks.

---

## Troubleshooting

### I do not have Claude Code installed

```bash
npm install -g @anthropic-ai/claude-code
```

### I need to confirm the API key is configured

Use a masked check instead of printing the key:

```bash
grep '^ANTHROPIC_API_KEY=' ~/.hyodo/.env | sed 's/=.*/=***configured***/'
```

### Commands do not appear

```bash
cd ~/.hyodo
claude
```

Then run:

```text
/start
```

---

## Next Steps

- [Full README](README.md)
- [Detailed guide](QUICK_START.md)
- [Anthropic proof map](docs/ANTHROPIC_PROOF.md)
- [3-minute demo script](docs/DEMO_SCRIPT_3_MIN.md)
- [Contributing guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

---

**HyoDo helps make AI-assisted code easier to inspect before it is trusted.**
