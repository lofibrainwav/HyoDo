---
description: "Multi-platform orchestration - vendor-neutral tier routing"
allowed-tools: Read, Grep, Bash(curl:*), Bash(hyodo:*)
impact: MEDIUM
tags: [multiplatform, orchestration, routing, cost-optimization]
---

# /multiplatform - multi-platform orchestration

> Route by risk and complexity tier. Provider names are adapters only.

Analyze `$ARGUMENTS` and route to the best **cost tier**.
Example providers: Ollama, Codex, Grok, Gemini, Claude, OpenAI, OpenCode, Cursor.

**Quality truth is the gate, not the model:** `hyodo check` · `hyodo safe` · CI.

---

## Tier hierarchy (vendor-neutral)

```
+-----------------------------------------------------+
|           CostAwareRouter (risk x complexity)       |
+-------------------------+---------------------------+
                          |
    +---------------------+---------------------+
    |                     |                     |
    v                     v                     v
+---------+         +---------+         +---------+
| FREE    |         |STANDARD |         | PREMIUM |
| local   |         | mid API |         | high    |
+----+----+         +----+----+         +----+----+
     |                   |                   |
     v                   v                   v
 lint/test/debug     implement/edit      design/review
 Ollama etc.         Codex/Gemini/Grok   Claude/GPT etc.
```

---

## Tier roles (providers are interchangeable)

| Tier | Example providers | Primary role | Trigger keywords |
|------|-------------------|--------------|------------------|
| **PREMIUM** | Claude, GPT, Gemini pro | Complex design, architecture, high-risk review | `design`, `architect`, `complex`, `review` |
| **FREE** | Ollama, local open models | Debug, test, lint, typecheck | `debug`, `test`, `lint`, `fix`, `type` |
| **STANDARD** | Codex, Grok, Gemini, mid-tier | Code generation, refactor, implement | `implement`, `refactor`, `generate`, `code` |
| **STANDARD** | OpenCode, Cursor agent | Fast search/explore/analyze | `search`, `find`, `explore`, `analyze` |

---

## Routing rules

### Rule 1: FREE first

```yaml
condition:
  task_type:
    - debug
    - test
    - lint
    - type_check
    - simple_fix
action: route_to_free_tier   # e.g. Ollama / local
cost: $0.00
post: hyodo check when code changes
```

### Rule 2: STANDARD lane

```yaml
condition:
  task_type:
    - implement
    - refactor
    - generate
  complexity: "<= 5"
action: route_to_standard_tier  # e.g. Codex / Grok / Gemini
post: hyodo check && hyodo safe
```

### Rule 3: PREMIUM only when needed

```yaml
condition:
  task_type:
    - architect
    - design
    - complex_review
  OR:
    complexity: "> 7"
    risk_score: "> 50"
action: route_to_premium_tier  # e.g. Claude / GPT / Gemini pro
post: hyodo check && hyodo safe && human review
```

> Percentage cost-savings figures are not a guaranteed public claim. This section
> only describes tier-routing intent.

---

## Local worker examples (FREE tier)

| Worker | Example model | Role | Triggers |
|--------|---------------|------|----------|
| Reviewer | qwen2.5-coder:7b | Code review | `review`, `refactor` |
| Debugger | deepseek-r1:7b | Bug tracing | `debug`, `bug`, `error` |
| Tester | qwen3:8b | Test generation | `test`, `pytest`, `coverage` |
| Implementer | codestral:latest | Fast generation | `implement`, `generate` |
| UI analyst | qwen3-vl:latest | UI analysis | `ui`, `screenshot`, `visual` |

---

## Output format

```yaml
multiplatform_routing:
  task: "$ARGUMENTS"
  analysis:
    keywords_detected:
      - "[keyword1]"
      - "[keyword2]"
    complexity_score: [0-10]
    risk_score: [0-100]
  routing_decision:
    primary_tier: [FREE|STANDARD|PREMIUM]
    example_provider: "[provider]"
    executor: "[worker]"
  cost_estimate:
    estimated_tokens: [n]
    estimated_cost: "$[cost]"
  parallel_possible: [true/false]
  fallback_tier: "[tier]"
  recommendation: "[notes]"
  post_gates:
    - hyodo check
    - hyodo safe
```

---

## Token-burn optimization

```yaml
optimization_strategies:
  free_first:
    description: "Prefer local/free for debug and test work"
    savings: "avoids premium model usage where local review is sufficient"
  parallel_distribution:
    description: "Split independent tasks across free/standard workers"
    savings: "depends on task independence and available local models"
  cache_hit:
    description: "Reuse similar prior results when safe"
    savings: "avoids repeated model calls"
  complexity_based:
    description: "Keep low complexity on STANDARD/FREE"
    savings: "routes low-risk work away from premium paths"
expected_total_savings: "workflow-dependent; benchmark before making public claims"
```

---

## Examples

### Example 1: debugging (FREE)

```bash
/multiplatform "fix failing pytest"

# routing result:
# tier: FREE
# provider example: Ollama
# cost: $0.00
```

### Example 2: implementation (STANDARD)

```bash
/multiplatform "implement a new API endpoint"

# routing result:
# tier: STANDARD
# provider example: Codex / Grok / Gemini
```

### Example 3: architecture (PREMIUM)

```bash
/multiplatform "design a microservice architecture"

# routing result:
# tier: PREMIUM
# provider example: Claude / GPT / Gemini pro
# reason: high-complexity design work
```

---

## Related files

- Chancellor V3: `packages/afo-core/api/chancellor_v2/orchestrator/`
- CostAwareRouter: `packages/afo-core/api/chancellor_v2/orchestrator/cost_aware_router.py`
- KeyTriggerRouter: `packages/afo-core/api/chancellor_v2/orchestrator/key_trigger_router.py`
- Local debugger skill: `.claude/agents/ollama-debugger.md`
