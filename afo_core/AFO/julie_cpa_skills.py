"""
Julie CPA Skills for AFO Kingdom Skills Registry

Specialized skills for tax analysis, IRS compliance, and accounting automation
integrated with Chancellor Graph and Trinity Score evaluation.
"""

from datetime import datetime

from AFO.afo_skills_registry import (
    AFOSkillCard,
    ExecutionMode,
    MCPConfig,
    PhilosophyScore,
    SkillCategory,
    SkillIOSchema,
    SkillParameter,
    SkillStatus,
    skills_registry,
)

# Julie CPA Associate Agent Skill
julie_associate_skill = AFOSkillCard(
    skill_id="skill_010_julie_associate",
    name="Julie Associate Agent",
    description="Data collection and initial tax analysis for Julie CPA workflow",
    category=SkillCategory.ANALYSIS_EVALUATION,
    execution_mode=ExecutionMode.ASYNC,
    philosophy_scores=PhilosophyScore(truth=85, goodness=90, beauty=80, serenity=95),
    input_schema=SkillIOSchema(
        parameters=[
            SkillParameter(
                name="client_data",
                type="object",
                description="Client information including tax year, filing status, income data",
                required=True,
            ),
            SkillParameter(
                name="tax_documents",
                type="array",
                description="List of tax documents and evidence links",
                required=True,
            ),
            SkillParameter(
                name="analysis_type",
                type="string",
                description="Type of tax analysis (standard_deduction, roth_conversion, etc.)",
                required=True,
            ),
        ]
    ),
    output_schema=SkillIOSchema(
        parameters=[
            SkillParameter(
                name="draft_analysis",
                type="object",
                description="Initial tax analysis draft with calculations and assumptions",
                required=True,
            ),
            SkillParameter(
                name="evidence_links",
                type="array",
                description="Validated evidence links supporting the analysis",
                required=True,
            ),
            SkillParameter(
                name="trinity_score",
                type="number",
                description="Trinity Score for the draft analysis",
                required=True,
            ),
        ]
    ),
    mcp_config=MCPConfig(
        enabled=True,
        tools=["tax_calculator", "document_analyzer", "irs_api_client"],
        resources=["irs_publications", "tax_databases"],
    ),
    status=SkillStatus.ACTIVE,
    version="1.0.0",
    created_at=datetime.now(),
    updated_at=datetime.now(),
)


# Julie CPA Manager Agent Skill
julie_manager_skill = AFOSkillCard(
    skill_id="skill_011_julie_manager",
    name="Julie Manager Agent",
    description="Strategic review and risk assessment for tax positions",
    category=SkillCategory.STRATEGIC_COMMAND,
    execution_mode=ExecutionMode.ASYNC,
    philosophy_scores=PhilosophyScore(truth=90, goodness=95, beauty=85, serenity=85),
    input_schema=SkillIOSchema(
        parameters=[
            SkillParameter(
                name="associate_draft",
                type="object",
                description="Draft analysis from Associate Agent",
                required=True,
            ),
            SkillParameter(
                name="evidence_links",
                type="array",
                description="Evidence supporting the analysis",
                required=True,
            ),
            SkillParameter(
                name="client_objectives",
                type="object",
                description="Client tax planning objectives and constraints",
                required=True,
            ),
        ]
    ),
    output_schema=SkillIOSchema(
        parameters=[
            SkillParameter(
                name="strategic_review",
                type="object",
                description="Strategic assessment with recommendations",
                required=True,
            ),
            SkillParameter(
                name="risk_assessment",
                type="object",
                description="Comprehensive risk analysis",
                required=True,
            ),
            SkillParameter(
                name="trinity_score",
                type="number",
                description="Updated Trinity Score after review",
                required=True,
            ),
            SkillParameter(
                name="gate_decision",
                type="string",
                description="AUTO_RUN or ASK decision based on Trinity Score",
                required=True,
            ),
        ]
    ),
    mcp_config=MCPConfig(
        enabled=True,
        tools=["risk_analyzer", "strategy_optimizer", "compliance_checker"],
        resources=["tax_strategy_databases", "risk_assessment_models"],
    ),
    status=SkillStatus.ACTIVE,
    version="1.0.0",
    created_at=datetime.now(),
    updated_at=datetime.now(),
)


# Julie CPA Auditor Agent Skill
julie_auditor_skill = AFOSkillCard(
    skill_id="skill_012_julie_auditor",
    name="Julie Auditor Agent",
    description="Regulatory compliance audit and final certification",
    category=SkillCategory.GOVERNANCE,
    execution_mode=ExecutionMode.ASYNC,
    philosophy_scores=PhilosophyScore(truth=95, goodness=98, beauty=90, serenity=90),
    input_schema=SkillIOSchema(
        parameters=[
            SkillParameter(
                name="associate_draft",
                type="object",
                description="Original draft analysis",
                required=True,
            ),
            SkillParameter(
                name="manager_review",
                type="object",
                description="Manager's strategic review",
                required=True,
            ),
            SkillParameter(
                name="evidence_bundle",
                type="object",
                description="Complete evidence bundle",
                required=True,
            ),
        ]
    ),
    output_schema=SkillIOSchema(
        parameters=[
            SkillParameter(
                name="final_deliverable",
                type="object",
                description="Final client-ready deliverable",
                required=True,
            ),
            SkillParameter(
                name="audit_trail",
                type="object",
                description="Complete audit trail with Evidence Bundle",
                required=True,
            ),
            SkillParameter(
                name="compliance_certificate",
                type="object",
                description="AICPA/IRS compliance certification",
                required=True,
            ),
            SkillParameter(
                name="sha256_hash",
                type="string",
                description="Cryptographic hash for audit trail immutability",
                required=True,
            ),
        ]
    ),
    mcp_config=MCPConfig(
        enabled=True,
        tools=["audit_trail_generator", "compliance_validator", "hash_generator"],
        resources=["irs_regulations", "aicpa_standards", "audit_databases"],
    ),
    status=SkillStatus.ACTIVE,
    version="1.0.0",
    created_at=datetime.now(),
    updated_at=datetime.now(),
)


# Tax Analysis Skill
tax_analysis_skill = AFOSkillCard(
    skill_id="skill_013_tax_analysis",
    name="Tax Analysis Engine",
    description="Comprehensive tax calculation and analysis for various scenarios",
    category=SkillCategory.ANALYSIS_EVALUATION,
    execution_mode=ExecutionMode.SYNC,
    philosophy_scores=PhilosophyScore(truth=92, goodness=88, beauty=85, serenity=90),
    input_schema=SkillIOSchema(
        parameters=[
            SkillParameter(
                name="tax_scenario",
                type="string",
                description="Type of tax analysis (federal, state, international)",
                required=True,
            ),
            SkillParameter(
                name="financial_data",
                type="object",
                description="Income, deductions, credits, and other financial data",
                required=True,
            ),
            SkillParameter(
                name="tax_year", type="string", description="Tax year for analysis", required=True
            ),
        ]
    ),
    output_schema=SkillIOSchema(
        parameters=[
            SkillParameter(
                name="tax_calculations",
                type="object",
                description="Detailed tax calculations with breakdowns",
                required=True,
            ),
            SkillParameter(
                name="optimization_suggestions",
                type="array",
                description="Tax optimization recommendations",
                required=True,
            ),
            SkillParameter(
                name="compliance_warnings",
                type="array",
                description="Potential compliance issues or warnings",
                required=True,
            ),
        ]
    ),
    mcp_config=MCPConfig(
        enabled=True,
        tools=["tax_calculator", "irs_api_client", "optimization_engine"],
        resources=["irs_tax_tables", "state_tax_databases", "tax_optimization_models"],
    ),
    status=SkillStatus.ACTIVE,
    version="1.0.0",
    created_at=datetime.now(),
    updated_at=datetime.now(),
)


# IRS Compliance Skill
irs_compliance_skill = AFOSkillCard(
    skill_id="skill_014_irs_compliance",
    name="IRS Compliance Validator",
    description="Real-time IRS regulation compliance checking and validation",
    category=SkillCategory.GOVERNANCE,
    execution_mode=ExecutionMode.ASYNC,
    philosophy_scores=PhilosophyScore(truth=97, goodness=98, beauty=88, serenity=92),
    input_schema=SkillIOSchema(
        parameters=[
            SkillParameter(
                name="tax_position",
                type="object",
                description="Tax position or strategy to validate",
                required=True,
            ),
            SkillParameter(
                name="regulatory_context",
                type="object",
                description="Applicable IRS regulations and notices",
                required=True,
            ),
            SkillParameter(
                name="evidence_links",
                type="array",
                description="Supporting evidence and citations",
                required=True,
            ),
        ]
    ),
    output_schema=SkillIOSchema(
        parameters=[
            SkillParameter(
                name="compliance_status",
                type="string",
                description="Compliance status (COMPLIANT, NON_COMPLIANT, UNCERTAIN)",
                required=True,
            ),
            SkillParameter(
                name="validation_details",
                type="object",
                description="Detailed compliance analysis and reasoning",
                required=True,
            ),
            SkillParameter(
                name="recommended_actions",
                type="array",
                description="Recommended actions for compliance",
                required=True,
            ),
            SkillParameter(
                name="confidence_score",
                type="number",
                description="Confidence level in the compliance assessment",
                required=True,
            ),
        ]
    ),
    mcp_config=MCPConfig(
        enabled=True,
        tools=["irs_regulation_parser", "compliance_checker", "citation_validator"],
        resources=["irs_code_database", "revenue_procedures", "court_rulings"],
    ),
    status=SkillStatus.ACTIVE,
    version="1.0.0",
    created_at=datetime.now(),
    updated_at=datetime.now(),
)


# Audit Trail Generator Skill
audit_trail_skill = AFOSkillCard(
    skill_id="skill_015_audit_trail",
    name="Audit Trail Generator",
    description="Generate immutable audit trails with cryptographic hashing",
    category=SkillCategory.SECURITY,
    execution_mode=ExecutionMode.SYNC,
    philosophy_scores=PhilosophyScore(truth=95, goodness=96, beauty=85, serenity=88),
    input_schema=SkillIOSchema(
        parameters=[
            SkillParameter(
                name="audit_data",
                type="object",
                description="Data to include in the audit trail",
                required=True,
            ),
            SkillParameter(
                name="evidence_bundle",
                type="object",
                description="Evidence bundle to hash and store",
                required=True,
            ),
            SkillParameter(
                name="metadata",
                type="object",
                description="Additional metadata for the audit trail",
                required=True,
            ),
        ]
    ),
    output_schema=SkillIOSchema(
        parameters=[
            SkillParameter(
                name="audit_trail_hash",
                type="string",
                description="SHA256 hash of the complete audit trail",
                required=True,
            ),
            SkillParameter(
                name="audit_certificate",
                type="object",
                description="Digital certificate with timestamp and verification data",
                required=True,
            ),
            SkillParameter(
                name="storage_location",
                type="string",
                description="Secure storage location of the audit trail",
                required=True,
            ),
        ]
    ),
    mcp_config=MCPConfig(
        enabled=True,
        tools=["hash_generator", "certificate_issuer", "secure_storage"],
        resources=["audit_databases", "cryptographic_services"],
    ),
    status=SkillStatus.ACTIVE,
    version="1.0.0",
    created_at=datetime.now(),
    updated_at=datetime.now(),
)


# Register Julie CPA Skills
def register_julie_cpa_skills() -> None:
    """Register all Julie CPA skills with the AFO Skills Registry."""

    julie_skills = [
        julie_associate_skill,
        julie_manager_skill,
        julie_auditor_skill,
        tax_analysis_skill,
        irs_compliance_skill,
        audit_trail_skill,
    ]

    registered_count = 0
    for skill in julie_skills:
        try:
            skills_registry.register(skill)
            registered_count += 1
            print(f"✅ Registered Julie CPA skill: {skill.name}")
        except Exception as e:
            print(f"❌ Failed to register skill {skill.name}: {e}")

    print(f"📋 Total Julie CPA skills registered: {registered_count}")
    return registered_count


# Auto-register skills on import
if __name__ != "__main__":
    register_julie_cpa_skills()


# Export skills for external use
__all__ = [
    "julie_associate_skill",
    "julie_manager_skill",
    "julie_auditor_skill",
    "tax_analysis_skill",
    "irs_compliance_skill",
    "audit_trail_skill",
    "register_julie_cpa_skills",
]
