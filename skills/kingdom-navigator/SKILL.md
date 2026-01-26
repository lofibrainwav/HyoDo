---
name: kingdom-navigator
description: This skill should be used when the user asks "where is", "find file", "navigate to", "project structure", "which file handles", or needs to locate specific functionality in the AFO Kingdom codebase. Provides intelligent navigation based on MAP_OF_KINGDOM.md and CONTEXT_COMPASS.yaml.
version: 1.0.0
license: MIT
compatibility:
  - claude-code
  - codex
  - cursor
metadata:
  category: navigation-discovery
  author: AFO Kingdom
  map_version: "2025.01"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  # MCP tools (optional - AFO Kingdom 환경에서만 지원)
  # - mcp__context7__*
standalone: true
---

# AFO Kingdom Navigator

Your guide to navigating the AFO Kingdom codebase. Uses the royal map and compass to find any destination.

## Kingdom Structure

```
/Users/brnestrm/AFO_Kingdom/
├── packages/                 # Core packages (monorepo)
│   ├── afo-core/            # Backend (FastAPI, Chancellor)
│   ├── trinity-os/          # Philosophy engine
│   ├── dashboard/           # Frontend (Next.js 16)
│   └── sixXon/              # CLI interface
├── .claude/                  # Claude Code configuration
│   ├── commands/            # 25 slash commands
│   ├── agents/              # Autonomous agents
│   └── mcp.json             # 9 MCP servers
├── skills/                   # 23 skill modules
├── scripts/                  # 400+ automation scripts
├── tools/                    # 44 tool packages
├── docs/                     # 240+ documentation files
└── tests/                    # Test suites
```

## Quick Navigation Guide

### By Domain

| Domain | Path | Key Files |
|--------|------|-----------|
| **Backend API** | `packages/afo-core/` | `api/`, `AFO/` |
| **Trinity Score** | `packages/trinity-os/trinity_os/` | `core/`, `servers/` |
| **Frontend UI** | `packages/dashboard/` | `src/app/`, `components/` |
| **CLI** | `packages/sixXon/` | `docs/SIXXON_*.md` |
| **MCP Servers** | `packages/trinity-os/trinity_os/servers/` | `*_mcp.py` |

### By Functionality

| Need | Location |
|------|----------|
| Trinity Score calculation | `packages/trinity-os/trinity_os/servers/trinity_score_mcp.py` |
| Chancellor orchestration | `packages/afo-core/api/chancellor_v2/` |
| 3 Strategists logic | `packages/afo-core/AFO/chancellor/` |
| Dashboard components | `packages/dashboard/src/components/` |
| API endpoints | `packages/afo-core/api/` |
| Skills definitions | `skills/*/SKILL.md` |
| Commands | `.claude/commands/*.md` |

### By File Type

| File Type | Glob Pattern |
|-----------|--------------|
| Python source | `packages/**/*.py` |
| TypeScript | `packages/dashboard/**/*.tsx` |
| Commands | `.claude/commands/*.md` |
| Skills | `skills/*/SKILL.md` |
| MCP servers | `**/servers/*_mcp.py` |
| Tests | `tests/**/*.py` |

## Reference Documents

| Document | Path | Purpose |
|----------|------|---------|
| **MAP_OF_KINGDOM** | `docs/MAP_OF_KINGDOM.md` | Complete documentation index |
| **CONTEXT_COMPASS** | `.claude/CONTEXT_COMPASS.yaml` | Navigation guide |
| **CLAUDE.md (Root)** | `CLAUDE.md` | Master guidelines |
| **SSOT** | `docs/AFO_FINAL_SSOT.md` | Single source of truth |

## Navigation Commands

Use these to explore:

```bash
# Find all Trinity-related files
Glob: **/trinity*.py

# Find Chancellor implementation
Grep: "class Chancellor"

# Find API endpoints
Grep: "@router\." path:packages/afo-core/api

# Find skill definitions
Glob: skills/*/SKILL.md
```

## MCP Server Locations

| Server | Path |
|--------|------|
| `afo-ultimate-mcp` | `trinity_os/servers/afo_ultimate_mcp_server.py` |
| `trinity-score-mcp` | `trinity_os/servers/trinity_score_mcp.py` |
| `afo-skills-mcp` | `trinity_os/servers/afo_skills_mcp.py` |
| `afo-obsidian-mcp` | `trinity_os/servers/obsidian_mcp.py` |
| `context7` | External (npx @upstash/context7-mcp) |
| `sequential-thinking` | External (npx) |
| `memory` | External (npx) |
| `mcp-docker-gateway` | Docker (111 tools) |

## Port Map (Local Kingdom)

| Service | Port | Package |
|---------|------|---------|
| Dashboard | 3000 | dashboard |
| Soul Engine API | 8010 | afo-core |
| PostgreSQL | 15432 | infrastructure |
| Redis | 6379 | infrastructure |
| Ollama | 11435 | infrastructure |

## Common Searches

**"Where is the Trinity Score calculated?"**
→ `packages/trinity-os/trinity_os/servers/trinity_score_mcp.py`

**"Where are the API routes?"**
→ `packages/afo-core/api/`

**"Where is the dashboard home page?"**
→ `packages/dashboard/src/app/page.tsx`

**"Where are the 3 strategists?"**
→ `packages/afo-core/AFO/chancellor/`

**"Where is the Claude configuration?"**
→ `.claude/` (commands, agents, mcp.json)

## Pro Tips

1. Use `Glob` for pattern-based file discovery
2. Use `Grep` for content-based search
3. Check `docs/MAP_OF_KINGDOM.md` for documentation index
4. Reference `.claude/CONTEXT_COMPASS.yaml` for context guidance
5. All paths are relative to `/Users/brnestrm/AFO_Kingdom/`
