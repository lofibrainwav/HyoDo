# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Governance Kill Switch
문명 락다운(Lockdown) 시스템.

Provides a global kill-switch mechanism to lock down the civilization
in case of extreme risk or emergency. Controlled by the Sovereign.
"""

import logging

logger = logging.getLogger("AFO.Governance.Sentry")


class CivilizationSentry:
    """The Guardian of the Kill Switch."""

    def __init__(self) -> None:
        self._locked: bool = False
        self._reason: str | None = None
        self._lock_count: int = 0

    def is_locked(self) -> bool:
        """Check if civilization is in lockdown."""
        return self._locked

    def lock(self, reason: str = "Emergency Protocol Activated") -> None:
        """Lock down the civilization."""
        if self._locked:
            logger.warning(f"Civilization already locked: {self._reason}")
            return

        self._locked = True
        self._reason = reason
        self._lock_count += 1
        logger.critical(f"🔒 CIVILIZATION LOCKDOWN ACTIVATED: {reason}")
        # In a real system, this might trigger widespread alerts or shutdown sequences

    def unlock(self) -> None:
        """Unlock the civilization (Restore Sovereignty)."""
        if not self._locked:
            return

        self._locked = False
        last_reason = self._reason
        self._reason = None
        logger.info(f"🔓 Civilization Unlocked. Previous reason: {last_reason}")

    def get_status(self) -> dict:
        """Get current sentry status."""
        return {
            "locked": self._locked,
            "reason": self._reason,
            "lock_count": self._lock_count,
        }


# Singleton Instance
sentry = CivilizationSentry()
