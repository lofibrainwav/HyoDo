
# 🏰 AFO Kingdom Final Architecture Report
## The LangGraph Chancellor System (승상 체제)

### 1. 👑 The Brain: LangGraph (Chancellor)
**Role**: State Management, Routing, Serenity (孝)
- **State**: Maintains the `Trinity Score` and Conversation History.
- **Routing**: Dynamically delegates to Strategists based on context.
- **Persistence**: Checkpointing for fault tolerance (永).
- **Auto-Run**: Enforces autonomous execution when alignment is high.

### 2. ⚔️ The Hands: Strategists (Nodes)
**Implementation**: CrewAI / AutoGen / LangChain
- **Jang Yeong-sil (Truth/Spear)**: Architecture & Strategy.
- **Yi Sun-sin (Goodness/Shield)**: Risk & Ethics.
- **Shin Saimdang (Beauty/Bridge)**: Narrative & UX.

### 3. 🛠️ The Tools: LangChain & MCP
**Role**: The Glue & The Toolkit
- **LangChain**: Connects LLMs to data/tools.
- **MCP Servers**: Standardized access to:
    - `afo-ultimate-mcp` (Filesystem, Docker, Process)
    - `afo-skills-mcp` (RAG, Search, Knowledge)
    - `playwright` (UI Automation)

---

## 🏛️ Operation Gwanggaeto Expansion (v2.5)

### 1. 善 (Goodness): Julie Royal Tax Engine
*   **Truth in Backend**: Tax logic moved from React to Python (`JulieService.py`).
*   **Perplexity Intelligence**: 2025 Federal/CA tax rules integrated (Surtax, QBI).
*   **Template Advice**: Standardized "If This, Then That" optimization (401k, HSA).
*   **Frontend**: `JulieTaxWidget.tsx` serves as a "Dumb Terminal" for Royal Truth.

### 2. 孝 (Serenity): The Vision Bridge
*   **Tech**: Playwright-based Visual Verification (`test_vision_bridge.py`).
*   **Role**: "The Commander's Eyes" - Automatically verifies UI manifestation.
*   **Self-Healing**: Detects 404s/Errors before Commander does.

### 3. 美 (Beauty): Sensory Immersion (Upcoming)
*   **Jade Bell**: Audio feedback (`use-sound`) for tactile experience.
*   **Glassmorphism**: Emerald-themed UI for financial peace of mind.

---
*"The brain, memory, and eyes are fully synchronized."*
