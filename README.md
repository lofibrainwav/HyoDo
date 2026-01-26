# HyoDo

> **Automated Code Review for AI-Assisted Development**

<p align="center">
  <a href="./i18n/ko/README.md">한국어</a> •
  <a href="./i18n/zh/README.md">中文</a> •
  <a href="./i18n/ja/README.md">日本語</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Works_with-Claude_Code-blueviolet" alt="Claude Code">
  <img src="https://img.shields.io/badge/Saves-50--70%25_AI_Costs-green" alt="Cost Savings">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

---

## Why HyoDo?

Writing code with AI assistants like Claude is fast, but how do you know if the code is **good**?

HyoDo automatically checks your code quality and gives you a simple score:

| Score | Meaning | What to do |
|:-----:|:--------|:-----------|
| **90+** | ✅ Good to go | Ship it! |
| **70-89** | ⚠️ Needs review | Double-check before merging |
| **< 70** | ❌ Issues found | Fix the problems first |

No more guessing. No more "it works on my machine."

---

## Quick Start

If you use [Claude Code](https://claude.ai/code) (Anthropic's AI coding assistant), just type:

```
/check
```

That's it. HyoDo analyzes your code and tells you if it's ready.

### Other Commands

| Command | What it does |
|:--------|:-------------|
| `/start` | Show help |
| `/check` | Run quality check |
| `/score` | See your score |
| `/safe` | Check for security issues |
| `/cost` | Estimate AI costs |

---

## What Does HyoDo Check?

HyoDo looks at three things:

### 1. Does it work? (35%)
- Type errors
- Logic bugs
- Failing tests

### 2. Is it safe? (35%)
- Security vulnerabilities
- Error handling
- Edge cases

### 3. Is it readable? (20%)
- Code style
- Documentation
- Naming conventions

Plus: Developer experience (8%) and long-term maintainability (2%).

---

## Installation

### For Claude Code Users

```bash
git clone https://github.com/lofibrainwav/HyoDo.git ~/.hyodo
```

Or one-click:

```bash
curl -sSL https://raw.githubusercontent.com/lofibrainwav/HyoDo/main/install.sh | bash
```

### Requirements

- [Claude Code](https://claude.ai/code) — Anthropic's official coding assistant
- [Ollama](https://ollama.ai) (optional) — For local AI analysis (keeps your code private)

---

## How It Works

```
Your Code
    ↓
HyoDo Analysis (checks 3 areas)
    ↓
Score (0-100)
    ↓
✅ Ship it  /  ⚠️ Review it  /  ❌ Fix it
```

All analysis happens locally. Your code never leaves your machine.

---

## FAQ

**Q: Do I need to pay for HyoDo?**
A: No, HyoDo is free and open source (MIT license).

**Q: Does it work with other AI assistants?**
A: Currently optimized for Claude Code. Other integrations coming soon.

**Q: What languages are supported?**
A: Python, TypeScript, JavaScript, and more. If Claude Code supports it, HyoDo can check it.

**Q: Is my code safe?**
A: Yes. HyoDo runs locally. Nothing is sent to external servers unless you explicitly configure it.

---

## Contributing

Want to help? See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — Use it however you want.

---

<details>
<summary>About the Name</summary>

**HyoDo (孝道)** is Korean for "The Way of Harmony" — writing code that just works, without friction.

The project draws inspiration from King Sejong's era of innovation, applying timeless principles to modern software:

- Think long-term
- Prepare for the worst
- Keep it simple

</details>

---

<p align="center">
  <strong>New here?</strong> Just type <code>/check</code> and see what happens.
</p>
