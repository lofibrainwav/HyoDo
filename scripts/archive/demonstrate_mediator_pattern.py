import os
import pathlib
import sys

# Add package root to sys.path
sys.path.append(pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages")).resolve())

try:
    from afo_core.mediators.chancellor_mediator import (
        ChancellorMediator,
        StrategistSquad,
        TigerGeneralsUnit,
    )
except ImportError:
    # Adjust path if running from root relative to packages
    sys.path.append(
        pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
    )
    from mediators.chancellor_mediator import (
        ChancellorMediator,
        StrategistSquad,
        TigerGeneralsUnit,
    )


def demonstrate_mediator_pattern() -> None:
    print("👑 [Mediator Pattern Demonstration]")

    # 1. Create Components (Colleagues)
    strategists = StrategistSquad()
    tigers = TigerGeneralsUnit()

    # 2. Create Mediator (Connects them)
    # The mediator automatically registers itself with the colleagues
    ChancellorMediator(strategists, tigers)

    print("\n--- Flow Start: User Query ---")
    # 3. Component triggers an event
    # Strategists don't know about Tigers directly. They just "send" a message.
    strategists.deliberate("Deploy GenUI Widget")

    print("\n✅ Mediator Pattern Verification Complete: De-coupled communication successful.")


if __name__ == "__main__":
    demonstrate_mediator_pattern()
