# Trinity Score: 90.0 (Established by Chancellor)
from abc import ABC, abstractmethod
from typing import Any, Protocol

from AFO.llm_router import LLMConfig


class LLMProvider(Protocol):
    """
    LLM Provider Protocol (眞: 봉인된 인터페이스)
    """

    async def generate_response(self, prompt: str, **kwargs: Any) -> str: ...


class BaseLLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers.
    Standardizes how the Router interacts with different models (strategy pattern).
    """

    @abstractmethod
    async def generate(
        self, query: str, config: LLMConfig, context: dict[str, Any] | None = None
    ) -> str:
        """
        Generate text response from the LLM.
        """
        pass

    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs: Any) -> str:
        """
        Public contract for response generation (Royal Standard).
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the provider is currently available (API keys set, service up).
        """
        pass
