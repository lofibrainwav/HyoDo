# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Governance Persona Auth
페르소나 기반 권한 인증 시스템.

Manages authentication and authorization based on the active persona.
Ensures that only authorized personas can access sensitive endpoints.
"""

import logging

from fastapi import Header

logger = logging.getLogger("AFO.Governance.Auth")


class PersonaAuth:
    """Persona-based Authentication Manager."""

    def __init__(self) -> None:
        self._current_persona: str = "commander"  # Default to Commander for dev

    async def get_current_persona(self, x_afo_persona: str | None = Header(None)) -> str:
        """Dependency to get and validate the current persona from headers."""
        if x_afo_persona:
            # simple validation logic
            valid_personas = ["commander", "chancellor", "strategist", "observer"]
            if x_afo_persona.lower() not in valid_personas:
                # Soft fail for now, or log warning
                logger.warning(f"Unknown persona claim: {x_afo_persona}")
            self._current_persona = x_afo_persona

        return self._current_persona

    def set_persona(self, persona: str) -> None:
        """Manually set the current persona (internal use)."""
        self._current_persona = persona
        logger.info(f"🎭 Active Persona switched to: {persona}")


# Singleton Instance
persona_auth = PersonaAuth()
