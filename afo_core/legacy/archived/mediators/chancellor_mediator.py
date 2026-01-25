# Trinity Score: 90.0 (Established by Chancellor)
from abc import ABC, abstractmethod
from typing import Any, Optional

# ==========================================
# 1. Mediator & Colleague Interfaces
# ==========================================


class Mediator(ABC):
    """Mediator Interface: Declares a method for communicating with components."""

    @abstractmethod
    def notify(self, sender: object, event: str, data: Any = None) -> None:
        pass


class Colleague(ABC):
    """Base Colleague: Components that communicate via the Mediator.
    They do not reference other Colleagues directly.
    """

    def __init__(self, mediator: Mediator | None = None) -> None:
        self._mediator = mediator

    @property
    def mediator(self) -> Mediator:
        if self._mediator is None:
            raise ValueError("Mediator not initialized")
        return self._mediator

    @mediator.setter
    def mediator(self, mediator: Mediator) -> None:
        self._mediator = mediator

    def send(self, event: str, data: Any = None) -> None:
        """Sends a notification to the mediator."""
        if self._mediator:
            self._mediator.notify(self, event, data)
        else:
            print(f"⚠️ [Colleague] No mediator set for {self.__class__.__name__}")


# ==========================================
# 2. Concrete Components (Colleagues)
# ==========================================


class StrategistSquad(Colleague):
    """Concrete Colleague: Represents the 3 Strategists (Zhuge, Sima, Zhou)."""

    def deliberate(self, query: str) -> None:
        print(f"🧠 [Strategists] Deliberating on: {query}")
        # After deliberation, they notify the mediator to proceed
        self.send("deliberation_complete", {"query": query, "strategy": "Secure Deployment"})


class TigerGeneralsUnit(Colleague):
    """Concrete Colleague: Represents the 5 Tigers (Execution)."""

    def execute_order(self, strategy_data: dict) -> None:
        print(f"🐯 [Tigers] Received Order: {strategy_data.get('strategy')}")
        print("⚔️ [Tigers] Executing... Done.")
        self.send("execution_complete", {"status": "Success"})


# ==========================================
# 3. Concrete Mediator
# ==========================================


class ChancellorMediator(Mediator):
    """Concrete Mediator: Coordinates the workflow between Strategists and Tigers.
    The 'Brain' of the interaction.
    """

    def __init__(self, strategists: StrategistSquad, tigers: TigerGeneralsUnit) -> None:
        self._strategists = strategists
        self._strategists.mediator = self

        self._tigers = tigers
        self._tigers.mediator = self

    def notify(self, sender: object, event: str, data: Any = None) -> None:
        if event == "deliberation_complete":
            print("👑 [Chancellor Mediator] Strategy approved. Forwarding to Tigers.")
            self._tigers.execute_order(data)

        elif event == "execution_complete":
            print("👑 [Chancellor Mediator] Execution confirmed. Logging result to Royal Archives.")
            # Could trigger another colleague like 'RoyalScribe' here
