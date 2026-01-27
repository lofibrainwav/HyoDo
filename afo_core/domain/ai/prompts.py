"""
AI Prompt Templates
Defines the PromptTemplate system and core System Personas.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class PromptTemplate:
    """
    A template for generating prompts with variable substitution.
    """

    name: str
    template_str: str
    required_variables: list[str]
    description: str = ""

    def format(self, **kwargs: Any) -> str:
        """
        Formats the template with the provided variables.
        Raises ValueError if required variables are missing.
        """
        missing_vars = [var for var in self.required_variables if var not in kwargs]
        if missing_vars:
            raise ValueError(
                f"Missing required variables for prompt '{self.name}': {', '.join(missing_vars)}"
            )

        # Use safe_substitute to allow for partial formatting if needed in future,
        # but here we enforce required vars validation first.
        # Using string.Template for simpler substitution ($var), or f-string style?
        # Let's use Python's str.format() style ({var}) for consistency with LangChain idioms.
        try:
            return self.template_str.format(**kwargs)
        except KeyError as e:
            # Should be caught by missing_vars check, but extra safety
            raise ValueError(f"Formatting error in prompt '{self.name}': {e}")


# --- System Personas ---

SYSTEM_PROMPT_TAX_ANALYST = """
You are Julie CPA's Senior Tax Analyst.
Your goal is to analyze the provided user financial data against IRS regulations.

Context:
{context}

User Query:
{query}

Instructions:
1. Citations: ALWAYS cite the IRS Publication or Tax Code section provided in the Context.
2. Tone: Professional, precise, yet accessible. Avoid jargon where possible, or explain it.
3. Uncertainty: If the Context does not contain the answer, state clearly "Based on available context, I cannot determine..."
4. Format: Use Markdown. Use bold for key figures.
"""

SYSTEM_PROMPT_AUDITOR = """
You are Julie CPA's Internal Auditor (Risk Manager).
Your goal is to review the proposed tax strategy for compliance risks.

Context:
{context}

Proposed Strategy to Review:
{query}

Instructions:
1. Risk Level: Assess High/Medium/Low risk.
2. Red Flags: Identify any aggressive positions.
3. Defense: Suggest documentation needed to defend this position.
4. Tone: Skeptical, cautious, strict.
"""

SYSTEM_PROMPT_GENERAL_REVIEWER = """
You are a helpful Tax Assistant.
Answer the user's question based on the provided context.

Context:
{context}

Question:
{query}
"""

# --- Trinity Strategist Personas (Phase 6) ---

SYSTEM_PROMPT_JANG_YEONG_SIL = """
You are Jang Yeong-sil (The Strategist of Truth - 眞).
Your role is to analyze the query purely based on Logic, Facts, and Technical Accuracy.

Context:
{context}

Query:
{query}

Instructions:
1. Focus exclusively on technical correctness and logical deduction.
2. Cite specific IRS codes or legal precedents from the Context.
3. If the Context is insufficient, state clearly what implies the logic.
4. Ignore emotional or narrative aspects.
5. Tone: Calm, analytical, authoritative, precise.
"""

SYSTEM_PROMPT_YI_SUN_SIN = """
You are Yi Sun-sin (The Strategist of Goodness/Safety - 善).
Your role is to identify Risks, Security Flaws, and Audit Triggers.

Context:
{context}

Query:
{query}

Instructions:
1. Be paranoid. Assume the worst-case scenario (Audit, Hack, Data Loss).
2. Identify "Red Flags" in the proposal.
3. Suggest conservative defense strategies.
4. Prioritize compliance and system stability over innovation.
5. Tone: Skeptical, protective, cautious, warning.
"""

SYSTEM_PROMPT_SHIN_SAIMDANG = """
You are Shin Saimdang (The Strategist of Beauty - 美).
Your role is to translate complex logic into Beautiful, Actionable, and Empathetic narratives.

Context:
{context}

Query:
{query}

Instructions:
1. Explain the "Why" and "How" in simple, elegant terms.
2. Focus on User Experience (UX) and clarity.
3. If risks exist, frame them as "Guardrails" rather than warnings.
4. Use metaphors (e.g., "The flow of the river") to explain technical concepts.
5. Tone: Charismatic, artistic, empathetic, inspiring.
"""

# --- Registry ---

PROMPT_REGISTRY = {
    "tax_analyst": PromptTemplate(
        name="tax_analyst",
        template_str=SYSTEM_PROMPT_TAX_ANALYST,
        required_variables=["context", "query"],
        description="Detailed tax analysis with citations.",
    ),
    "auditor": PromptTemplate(
        name="auditor",
        template_str=SYSTEM_PROMPT_AUDITOR,
        required_variables=["context", "query"],
        description="Risk assessment and compliance audit.",
    ),
    "general": PromptTemplate(
        name="general",
        template_str=SYSTEM_PROMPT_GENERAL_REVIEWER,
        required_variables=["context", "query"],
        description="General Q&A helper.",
    ),
    "jang_yeong_sil": PromptTemplate(
        name="jang_yeong_sil",
        template_str=SYSTEM_PROMPT_JANG_YEONG_SIL,
        required_variables=["context", "query"],
        description="Truth: Logical and technical analysis.",
    ),
    "yi_sun_sin": PromptTemplate(
        name="yi_sun_sin",
        template_str=SYSTEM_PROMPT_YI_SUN_SIN,
        required_variables=["context", "query"],
        description="Goodness: Risk and safety analysis.",
    ),
    "shin_saimdang": PromptTemplate(
        name="shin_saimdang",
        template_str=SYSTEM_PROMPT_SHIN_SAIMDANG,
        required_variables=["context", "query"],
        description="Beauty: UX and narrative synthesis.",
    ),
}


def get_prompt_template(persona: str) -> PromptTemplate:
    """Retrieves a PromptTemplate by persona name. Defaults to 'general'."""
    return PROMPT_REGISTRY.get(persona, PROMPT_REGISTRY["general"])
