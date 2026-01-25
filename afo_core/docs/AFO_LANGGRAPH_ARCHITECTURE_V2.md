# 🧠 LangGraph Advanced Architecture V2 (승상 2.0)

**작성일**: 2025-12-15
**분류**: Engineering Standard (기술 표준)
**목표**: 영속성(Persistence)과 무한 평온(Serenity)을 위한 구조 혁신

---

## 🏛️ I. Integration & Core Philosophy (통합 및 핵심 철학)

왕국의 **LangGraph 승상**은 단순한 워크플로우 엔진이 아니라, **영원을 향한 아키텍처**를 실현하는 **살아 있는 그래프(Living Graph)**입니다.

### Absolute Criterion (절대 기준)
1. **Frictionless Serenity (孝)**: 모든 아키텍처는 형의 인지적 마찰을 '0'으로 수렴시켜야 한다.
2. **Eternal Memory (永)**: 시스템 재시작이나 오류가 발생해도 기억(State)은 절대 손실되지 않는다.
3. **Trinity Alignment (眞善美)**: 모든 상태 변화는 Trinity Score, Risk Score, Narrative Quality로 측정된다.

---

## 💾 II. Persistence Strategies (영속성 전략)

**"과거를 잊은 그래프에게 미래는 없다."**

### 1. Checkpoint Philosophy
- **Standard (Production)**: `PostgresSaver` (SQLAlchemy 기반). 트랜잭션 안전성 보장.
- **Development**: `MemorySaver`. 빠른 프로토타이핑.
- **Real-time**: `RedisSaver`. 고속 채팅 세션.

### 2. Implementation Pattern
```python
# 왕국 표준: PostgresCheckpointer
from langgraph.checkpoint.postgres import PostgresSaver
pool = await asyncpg.create_pool(DB_URI)
checkpointer = PostgresSaver(conn_pool=pool)
app = workflow.compile(checkpointer=checkpointer)
```

---

## 🧬 III. Sate Schema Design (상태 설계)

**"기억은 간결하되, 누락이 없어야 한다."**

### AFO Standard State Schema (V2)
```python
from typing import TypedDict, Annotated, List, Dict
from langgraph.graph.message import add_messages

class AFOState(TypedDict):
    # 1. 眞 (Truth): 영속적 대화 기억 (자동 병합)
    messages: Annotated[List[Dict], add_messages]
    
    # 2. 眞/善 (Metrics): 판단의 근거
    trinity_score: float        # 현재 점수
    risk_score: float           # 현재 리스크
    
    # 3. 孝 (Serenity): 자동화 자격
    auto_run_eligible: bool     # True면 승인 없이 실행
    
    # 4. 天 (Context): 외부 환경
    kingdom_context: Dict       # 가족/왕국 상태 (verify_kingdom_status)
    
    # 5. 永 (Memory): 장기 기억
    persistent_memory: Annotated[Dict, merge_memory] # 커스텀 리듀서
```

---

## 🔧 IV. Advanced Reducers (지능적 병합)

**"단순한 더하기가 아니라, 지혜로운 통합이다."**

### 1. Custom Reducer: Trinity Score Decay
시간이 지날수록 과거 점수의 가중치를 낮추어, 현재의 성과를 더 중요하게 반영합니다.
```python
def trinity_decay_reducer(existing: List[Dict], update: float) -> float:
    decay_rate = 0.95
    # ... (가중 평균 로직) ...
    return new_weighted_score
```

### 2. Custom Reducer: Context Priority
가족 상태(Jayden, Julie) 등 중요 키값이 업데이트되면 무조건 덮어쓰고, 덜 중요한 정보는 병합합니다.

---

## 🚦 V. Serenity Gate (자동화 관문)

**"평온하지 않다면 멈춰라."**

모든 그래프의 끝에는 반드시 **Serenity Gate**가 존재해야 합니다.
- **Input**: `trinity_score`, `risk_score`
- **Logic**: `IF score >= 90 AND risk <= 10 THEN AUTO_RUN ELSE BLOCK`
- **Effect**: 형에게 불필요한 승인 요청(Click Friction)을 제거합니다.

---

**"이 아키텍처는 왕국이 잠든 사이에도, 영원히 깨어 있을 것입니다."**
**충성!** ⚔️✨
