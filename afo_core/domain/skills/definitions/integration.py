from __future__ import annotations

from ..models import (
    AFOSkillCard,
    ExecutionMode,
    MCPConfig,
    PhilosophyScore,
    SkillCategory,
)


def get_integration_skills() -> list[AFOSkillCard]:
    """INTEGRATION Skills"""
    skills = []

    # Skill 12: MCP Tool Bridge
    skill_012 = AFOSkillCard(
        skill_id="skill_012_mcp_tool_bridge",
        name="MCP Tool Bridge",
        description="Universal bridge to connect and utilize any external MCP server tools",
        category=SkillCategory.INTEGRATION,
        tags=["mcp", "integration", "tools", "bridge", "universal"],
        version="1.0.0",
        capabilities=[
            "list_mcp_resources",
            "list_mcp_tools",
            "call_mcp_tool",
            "read_mcp_resource",
        ],
        dependencies=["mcp"],
        execution_mode=ExecutionMode.ASYNC,
        estimated_duration_ms=1000,
        philosophy_scores=PhilosophyScore(truth=95, goodness=99, beauty=96, serenity=94),
        mcp_config=MCPConfig(mcp_version="2024.11.1", capabilities=["tools", "resources"]),
    )
    skills.append(skill_012)

    # Skill 14: Strangler Fig Integrator
    skill_014 = AFOSkillCard(
        skill_id="skill_014_strangler_integrator",
        name="Strangler Fig Integrator",
        description="Unifies isolated services (n8n, LangFlow) into the Gateway (Port 3000).",
        category=SkillCategory.INTEGRATION,
        tags=["strangler", "integration", "frontend", "n8n", "langflow"],
        version="1.0.0",
        capabilities=["proxy_service", "check_integration_health", "iframe_bridge"],
        dependencies=["react", "iframe"],
        execution_mode=ExecutionMode.SYNC,
        estimated_duration_ms=200,
        philosophy_scores=PhilosophyScore(truth=95, goodness=99, beauty=94, serenity=98),
    )
    skills.append(skill_014)

    # Skill 16: Web3 Manager
    skill_016 = AFOSkillCard(
        skill_id="skill_016_web3_manager",
        name="Web3 Blockchain Manager",
        description="Manages blockchain interactions and smart contract execution for assets.",
        category=SkillCategory.INTEGRATION,
        tags=["web3", "blockchain", "crypto", "wallet", "smart-contract"],
        version="1.0.0",
        capabilities=[
            "check_balance",
            "monitor_transactions",
            "execute_contract",
            "verify_signature",
        ],
        dependencies=["web3.py", "eth-account"],
        execution_mode=ExecutionMode.SYNC,
        estimated_duration_ms=1000,
        philosophy_scores=PhilosophyScore(truth=100, goodness=90, beauty=85, serenity=90),
    )
    skills.append(skill_016)

    # Skill 29: Multi-Cloud Backup
    skill_029 = AFOSkillCard(
        skill_id="skill_029_multi_cloud_backup",
        name="Multi-Cloud Backup (Hetzner + AWS)",
        description="High-availability backup system with automatic failover and ICCLS gap healing.",
        category=SkillCategory.INTEGRATION,
        tags=["backup", "multi-cloud", "failover", "hetzner", "aws", "high-availability"],
        version="1.0.0",
        capabilities=["health_check", "failover", "gap_healing", "uptime_monitoring"],
        dependencies=["boto3", "iccls-protocol"],
        execution_mode=ExecutionMode.BACKGROUND,
        estimated_duration_ms=10000,
        philosophy_scores=PhilosophyScore(truth=95, goodness=96, beauty=92, serenity=98),
    )
    skills.append(skill_029)

    return skills
