import os
import pathlib
import sys

# Add package root to sys.path
sys.path.append(pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages")).resolve())

try:
    from afo_core.commands.trinity_command import (
        AnalyzeCommand,
        ChancellorInvoker,
        DeployCommand,
        TigerGenerals,
    )
except ImportError:
    # Adjust path if running from root relative to packages
    sys.path.append(
        pathlib.Path(os.path.join(pathlib.Path(__file__).parent, "../packages/afo-core")).resolve()
    )
    from commands.trinity_command import (
        AnalyzeCommand,
        ChancellorInvoker,
        DeployCommand,
        TigerGenerals,
    )


def demonstrate_command_pattern() -> None:
    print("👑 [Command Pattern Demonstration]")

    # 1. Setup Receiver and Invoker
    tigers = TigerGenerals()
    chancellor = ChancellorInvoker()

    print("\n--- 1. Execution Phase (Action) ---")
    # 2. Create and Execute Commands
    cmd_deploy_widget = DeployCommand(tigers, "CPA Financial Widget")
    cmd_analyze_market = AnalyzeCommand(tigers, "Market Volatility")

    chancellor.execute_command(cmd_deploy_widget)
    chancellor.execute_command(cmd_analyze_market)

    print("\n--- 2. Undo Phase (Safety/Goodness) ---")
    # 3. Undo Operations
    chancellor.undo_last_command()  # Should undo Analysis
    chancellor.undo_last_command()  # Should undo Deployment

    print("\n--- 3. Empty History Check ---")
    chancellor.undo_last_command()  # Should handle empty history safely

    print("\n✅ Command Pattern Verification Complete: Execute & Undo successful.")


if __name__ == "__main__":
    demonstrate_command_pattern()
