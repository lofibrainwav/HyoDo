# Trinity Score: 90.0 (Established by Chancellor)
from abc import ABC, abstractmethod


# ==========================================
# 1. Command Interface
# ==========================================
class Command(ABC):
    """Abstract Command: Declares an interface for executing an operation.
    Must support execute() and undo().
    """

    @abstractmethod
    def execute(self) -> str:
        """Executes the command logic."""
        pass

    @abstractmethod
    def undo(self) -> str:
        """Reverses the command logic (Graceful Degradation)."""
        pass


# ==========================================
# 2. Receiver (The Business Logic)
# ==========================================
class TigerGenerals:
    """Receiver: The object that knows how to perform the operations.
    (Simulating the 5 Tigers Execution)
    """

    def deploy_resources(self, resource: str) -> str:
        return f"[Ma Chao 孝] Deployed {resource} (Seamlessly)."

    def revoke_resources(self, resource: str) -> str:
        return f"[Ma Chao 孝] Revoked {resource} (Rollback)."

    def analyze_risk(self, data: str) -> str:
        return f"[Zhang Fei 善] Risk Analysis Complete for {data}."


# ==========================================
# 3. Concrete Commands
# ==========================================
class DeployCommand(Command):
    """Concrete Command: Binds a specific action (Deploy) to the Receiver."""

    def __init__(self, receiver: TigerGenerals, resource: str) -> None:
        self._receiver = receiver
        self._resource = resource

    def execute(self) -> str:
        return self._receiver.deploy_resources(self._resource)

    def undo(self) -> str:
        return self._receiver.revoke_resources(self._resource)


class AnalyzeCommand(Command):
    """Concrete Command: Analyzes risk (Read-only, Undo does nothing conceptually, or logs)."""

    def __init__(self, receiver: TigerGenerals, target: str) -> None:
        self._receiver = receiver
        self._target = target

    def execute(self) -> str:
        return self._receiver.analyze_risk(self._target)

    def undo(self) -> str:
        return f"[Zhang Fei 善] Undo Analysis (Cleared Cache for {self._target})."


# ==========================================
# 4. Invoker (Chancellor)
# ==========================================
class ChancellorInvoker:
    """Invoker: Asks the command to carry out the request.
    Maintains a history for Undo functionality.
    """

    def __init__(self) -> None:
        self._history: list[Command] = []

    def execute_command(self, command: Command) -> None:
        result = command.execute()
        print(f"👑 [Chancellor] Executing: {result}")
        self._history.append(command)

    def undo_last_command(self) -> None:
        if not self._history:
            print("👑 [Chancellor] No commands to undo.")
            return

        command = self._history.pop()
        result = command.undo()
        print(f"👑 [Chancellor] Undoing: {result}")
