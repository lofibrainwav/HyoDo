from __future__ import annotations

from .config import MiproConfig
from .optimizer import MiproOptimizer

"""MIPROv2 Factory for creating optimizers."""


# Default configuration
default_config = MiproConfig(auto="light")

# Default optimizer instance
mipro_optimizer: MiproOptimizer = MiproOptimizer(default_config)


def create_optimizer(config: MiproConfig = default_config) -> MiproOptimizer:
    """Create a MIPROv2 optimizer with the given configuration.

    Args:
        config: Configuration for the optimizer

    Returns:
        Configured MiproOptimizer instance
    """
    return MiproOptimizer(config)
