"""API Compatibility Providers

각종 데이터 제공자들 (Philosophy, Port, Persona, Rules, Architecture, Stats).
"""

from .philosophy import PhilosophyDataProvider
from .port import PortDataProvider

__all__ = [
    "PhilosophyDataProvider",
    "PortDataProvider",
]
