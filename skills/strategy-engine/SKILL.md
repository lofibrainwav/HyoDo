---
name: strategy-engine
description: 4-stage command triage and orchestration using LangGraph with Redis checkpointing. Routes decisions through 3 strategists.
license: MIT
compatibility:
  - claude-code
  - codex
  - cursor
metadata:
  version: "2.3.0"
  category: strategic-command
  author: AFO Kingdom
  strategists:
    - jang_yeong_sil
    - yi_sun_sin
    - shin_saimdang
  philosophy_scores:
    truth: 96
    goodness: 94
    beauty: 93
    serenity: 95
---

# LangGraph Strategy Engine (Chancellor Graph)

The strategic command center of AFO Kingdom, orchestrating decisions through the wisdom of 3 legendary strategists.

## The 3 Strategists

| Strategist | Korean | Role | Specialty |
|------------|--------|------|-----------|
| Jang Yeong-sil | 장영실 | Prime Strategist | Long-term planning, complex analysis |
| Yi Sun-sin | 이순신 | Risk Strategist | Risk assessment, defensive measures |
| Shin Saimdang | 신사임당 | UX Strategist | Quick decisions, user experience |

## 4-Stage Command Triage

```
[User Command] → [Parse] → [Triage] → [Strategize] → [Execute]
                    ↓          ↓           ↓
               [Intent]   [Priority]  [Consensus]
                    ↓          ↓           ↓
               [Context]  [Risk Score] [Decision]
```

### Stage 1: Parse
- Natural language understanding
- Intent extraction
- Context gathering

### Stage 2: Triage
- Priority classification (P0-P3)
- Risk assessment
- Resource requirements

### Stage 3: Strategize
- 3-strategist consensus
- Trinity Score calculation
- Decision routing (AUTO_RUN/ASK/BLOCK)

### Stage 4: Execute
- Action execution
- State checkpointing
- Result verification

## Redis Checkpointing

All conversation states are persisted to Redis for:
- Stateful multi-turn conversations
- Crash recovery
- Audit trail

## Usage

```python
from AFO.chancellor import ChancellorGraph

chancellor = ChancellorGraph()
result = await chancellor.invoke({
    "command": "Optimize the database queries",
    "context": {"current_latency": "500ms"}
})

print(f"Decision: {result['decision']}")
print(f"Strategist: {result['lead_strategist']}")
print(f"Plan: {result['action_plan']}")
```

## Decision Criteria

The strategists vote based on:
- **Jang Yeong-sil**: Considers long-term implications
- **Yi Sun-sin**: Evaluates risks and contingencies
- **Shin Saimdang**: Assesses immediate feasibility

Consensus requires 2/3 agreement for AUTO_RUN.
