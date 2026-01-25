---
name: strategy-engine
description: 4-stage command triage and orchestration using LangGraph with Redis checkpointing. Routes decisions through 세종대왕의 3 전략가.
license: MIT
compatibility:
  - claude-code
  - codex
  - cursor
metadata:
  version: "3.0.0"
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

The strategic command center of AFO Kingdom, orchestrating decisions through 세종대왕의 정신 (Spirit of King Sejong).

## 세종대왕의 3 전략가

| Strategist | Korean | Role | Specialty |
|------------|--------|------|-----------|
| 장영실 (蔣英實) | Jang Yeong-sil | 眞 Sword ⚔️ | 측우기의 정밀함 - 기술적 정확성, 검증, 아키텍처 |
| 이순신 (李舜臣) | Yi Sun-sin | 善 Shield 🛡️ | 거북선의 수호 - 안전성, 리스크 평가, 게이트키핑 |
| 신사임당 (申師任堂) | Shin Saimdang | 美 Bridge 🌉 | 초충도의 예술 - UX, 가독성, 커뮤니케이션 |

## 4-Stage Command Triage

```text
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

- 3-strategist consensus (세종대왕의 정신)
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

- **장영실 (眞)**: "이 설계가 3년 후에도 유효한가? 기술 부채가 발생하는가?"
- **이순신 (善)**: "최악의 경우 무슨 일이 발생하는가? 테스트가 충분한가?"
- **신사임당 (美)**: "사용자가 이해할 수 있는가? 복잡성을 숨길 수 있는가?"

Consensus requires 2/3 agreement for AUTO_RUN.

## 세종대왕의 정신 통합

```text
┌─────────────────────────────────────────────────────┐
│              세종대왕의 정신 (世宗大王)                │
│  "백성을 위한 실용적 혁신과 문화적 융성"              │
├─────────────────────────────────────────────────────┤
│                                                     │
│   ⚔️ 장영실 (眞)     🛡️ 이순신 (善)    🌉 신사임당 (美)  │
│   측우기의 정밀함     거북선의 수호     초충도의 예술   │
│                                                     │
│   기술적 정확성      안전성 보장       UX 우수성      │
│   검증 가능성        리스크 최소화     가독성 확보    │
│   아키텍처 일관성    롤백 가능성       문서화 품질    │
│                                                     │
└─────────────────────────────────────────────────────┘
```
