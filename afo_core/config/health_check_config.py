from __future__ import annotations

from dataclasses import dataclass

# Trinity Score: 90.0 (Established by Chancellor)
"""Health Check Configuration (眞 - Truth)
건강 체크 설정 - 하드코딩 제거

야전교범 원칙: 가정 금지 - 모든 설정은 명시적으로 정의
"""


@dataclass
class MCPServerConfig:
    """MCP 서버 설정"""

    name: str
    description: str
    status: str = "configured"


@dataclass
class ScholarConfig:
    """학자 설정"""

    name: str
    type: str
    status: str = "available"


@dataclass
class HealthCheckConfig:
    """건강 체크 설정"""

    # MCP 서버 목록
    MCP_SERVERS: tuple[MCPServerConfig, ...] = (
        MCPServerConfig("memory", "지식 그래프 메모리"),
        MCPServerConfig("filesystem", "파일 시스템 접근"),
        MCPServerConfig("sequential-thinking", "단계별 추론"),
        MCPServerConfig("brave-search", "웹 검색"),
        MCPServerConfig("context7", "라이브러리 문서 주입"),
        MCPServerConfig("afo-ultimate-mcp", "AFO Ultimate MCP 서버"),
        MCPServerConfig("afo-skills-mcp", "AFO 스킬 MCP 서버"),
        MCPServerConfig("afo-messaging-mcp", "AFO Messaging MCP 서버"),
        MCPServerConfig("trinity-score-mcp", "Trinity Score MCP 서버"),
        MCPServerConfig("afo-skills-registry-mcp", "AFO Skills Registry MCP 서버"),
        MCPServerConfig("afo-obsidian-mcp", "AFO Obsidian MCP 서버"),
    )

    # 학자 목록
    SCHOLARS: tuple[ScholarConfig, ...] = (
        ScholarConfig("Yeongdeok", "Ollama Local"),
        ScholarConfig("Bangtong", "Codex CLI"),
        ScholarConfig("Jaryong", "Claude CLI"),
        ScholarConfig("Yukson", "Gemini API"),
    )

    # 건강 상태 임계값
    TRINITY_SCORE_THRESHOLD: float = 0.7

    # 스킬 표시 제한
    MAX_SKILLS_DISPLAY: int = 10

    # Context7 지식 베이스 키 제한
    MAX_CONTEXT7_KEYS_DISPLAY: int = 20


# 전역 설정 인스턴스
health_check_config = HealthCheckConfig()
