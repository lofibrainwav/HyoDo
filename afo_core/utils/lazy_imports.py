from __future__ import annotations

import importlib
import logging
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""Lazy Import 모듈 - 무거운 라이브러리 지연 로딩
AFO Ascension Protocol - Phase 1.2

기능:
- AutoGen, CrewAI, LangGraph 등 무거운 모듈 Lazy 로딩
- 서버 시작 시간 최적화 (5초 → 1.5초 목표)
- 메모리 사용량 감소
- Graceful degradation 지원
"""


logger = logging.getLogger(__name__)


class LazyModule:
    """지연 로딩 모듈 클래스

    사용법:
        autogen = LazyModule("autogen")
        agent = autogen.AssistantAgent(...)  # 여기서 실제 import 발생
    """

    def __init__(self, module_name: str, fallback: Any = None) -> None:
        """Args:
        module_name: 실제 import할 모듈 이름
        fallback: import 실패 시 사용할 대체 객체

        """
        self._module_name = module_name
        self._module: Any | None = None
        self._fallback = fallback
        self._import_error: Exception | None = None

    def __getattr__(self, name: str) -> Any:
        """속성 접근 시 실제 모듈 로딩"""
        if self._module is None:
            self._load_module()

        if self._module is not None:
            return getattr(self._module, name)
        elif self._fallback is not None:
            return getattr(self._fallback, name)
        else:
            raise AttributeError(f"module '{self._module_name}' has no attribute '{name}'")

    def _load_module(self) -> None:
        """실제 모듈 로딩"""
        try:
            self._module = importlib.import_module(self._module_name)
            logger.info(f"✅ Lazy loaded module: {self._module_name}")
        except ImportError as e:
            self._import_error = e
            if self._fallback is None:
                # 서버 시작 시점에서는 조용히 실패 (optional dependency)
                if hasattr(sys, "_getframe") and "api_server" in str(
                    sys._getframe(0).f_code.co_filename
                ):
                    # 서버 시작 시에는 로깅하지 않음
                    pass
                else:
                    logger.debug(f"Failed to import {self._module_name}: {e}")
                # 빈 모듈로 설정하여 AttributeError 방지
                self._module = type(sys)("dummy_module")
            else:
                logger.info(f"ℹ️  Using fallback for {self._module_name}")
                self._module = self._fallback

    def is_available(self) -> bool:
        """모듈 사용 가능 여부 확인"""
        if self._module is None:
            self._load_module()
        return self._import_error is None

    def get_error(self) -> Exception | None:
        """Import 에러 반환"""
        return self._import_error


class LazyFunction:
    """지연 로딩 함수 클래스

    사용법:
        result = lazy_autogen_func("param")  # 여기서 실제 import 발생
    """

    def __init__(self, module_name: str, func_name: str, fallback: Callable | None = None) -> None:
        self._module_name = module_name
        self._func_name = func_name
        self._fallback = fallback
        self._func: Callable | None = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """함수 호출 시 실제 모듈/함수 로딩"""
        if self._func is None:
            try:
                module = importlib.import_module(self._module_name)
                self._func = getattr(module, self._func_name)
                logger.info(f"✅ Lazy loaded function: {self._module_name}.{self._func_name}")
            except (ImportError, AttributeError) as e:
                if self._fallback:
                    logger.info(f"ℹ️  Using fallback for {self._module_name}.{self._func_name}")
                    self._func = self._fallback
                else:
                    logger.warning(f"⚠️  Failed to load {self._module_name}.{self._func_name}: {e}")
                    raise e

        return self._func(*args, **kwargs)


# ============================================================================
# AI/ML 프레임워크 Lazy 모듈들
# ============================================================================

# AutoGen (무거운 라이브러리)
try:
    autogen = LazyModule("autogen")
    autogen_agentchat = LazyModule("autogen_agentchat")
    autogen_core = LazyModule("autogen_core")
    autogen_ext = LazyModule("autogen_ext")
except ImportError:
    # Fallback 빈 모듈
    autogen = LazyModule("autogen", type(sys)("dummy_autogen"))
    autogen_agentchat = LazyModule("autogen_agentchat", type(sys)("dummy_autogen_agentchat"))
    autogen_core = LazyModule("autogen_core", type(sys)("dummy_autogen_core"))
    autogen_ext = LazyModule("autogen_ext", type(sys)("dummy_autogen_ext"))

# CrewAI
try:
    crewai = LazyModule("crewai")
except ImportError:
    crewai = LazyModule("crewai", type(sys)("dummy_crewai"))

# LangChain/LangGraph
try:
    langchain = LazyModule("langchain")
    langchain_core = LazyModule("langchain_core")
    langgraph = LazyModule("langgraph")
except ImportError:
    langchain = LazyModule("langchain", type(sys)("dummy_langchain"))
    langchain_core = LazyModule("langchain_core", type(sys)("dummy_langchain_core"))
    langgraph = LazyModule("langgraph", type(sys)("dummy_langgraph"))

# LlamaIndex
try:
    llama_index = LazyModule("llama_index")
    llama_index_core = LazyModule("llama_index.core")
except ImportError:
    llama_index = LazyModule("llama_index", type(sys)("dummy_llama_index"))
    llama_index_core = LazyModule("llama_index.core", type(sys)("dummy_llama_index_core"))

# ============================================================================
# 기타 무거운 라이브러리들
# ============================================================================

# OpenAI (이미 최적화되어 있지만 일관성을 위해)
try:
    openai = LazyModule("openai")
except ImportError:
    openai = LazyModule("openai", type(sys)("dummy_openai"))

# Anthropic Claude
try:
    anthropic = LazyModule("anthropic")
except ImportError:
    anthropic = LazyModule("anthropic", type(sys)("dummy_anthropic"))

# Vector databases
# chromadb is intentionally NOT imported: removed from dependencies (Qdrant SSOT).
chromadb = LazyModule("chromadb", type(sys)("dummy_chromadb"))
try:
    qdrant_client = LazyModule("qdrant_client")
except ImportError:
    qdrant_client = LazyModule("qdrant_client", type(sys)("dummy_qdrant_client"))

# ============================================================================
# 유틸리티 함수들
# ============================================================================


def get_available_modules() -> dict[str, bool]:
    """사용 가능한 모듈들 상태 확인"""
    modules = {
        "autogen": autogen.is_available(),
        "crewai": crewai.is_available(),
        "langchain": langchain.is_available(),
        "langgraph": langgraph.is_available(),
        "llama_index": llama_index.is_available(),
        "openai": openai.is_available(),
        "anthropic": anthropic.is_available(),
        "chromadb": False,  # removed dependency; Qdrant is SSOT
        "qdrant_client": qdrant_client.is_available(),
    }
    return modules


def preload_critical_modules() -> None:
    """중요한 모듈들 미리 로딩
    서버 시작 시 호출하여 초기 지연 최소화
    """
    critical_modules = [
        "openai",  # 가장 많이 사용
        "anthropic",  # 두 번째로 많이 사용
        "langchain_core",  # 기본 LangChain
    ]

    for module_name in critical_modules:
        try:
            module = globals().get(module_name)
            if module and hasattr(module, "is_available"):
                module.is_available()  # 트리거하여 로딩
        except Exception as e:
            logger.warning(f"Failed to preload {module_name}: {e}")


def create_fallback_function(func_name: str, error_msg: str | None = None) -> Callable[..., Any]:
    """대체 함수 생성"""

    def fallback(*args: Any, **kwargs: Any) -> Any:
        msg = error_msg or f"Function {func_name} is not available"
        logger.warning(msg)
        raise NotImplementedError(msg)

    return fallback


# ============================================================================
# 테스트 및 디버깅
# ============================================================================

if __name__ == "__main__":
    print("🧪 Lazy Import 모듈 테스트 시작...")

    # 모듈 상태 확인
    print("\n📦 모듈 사용 가능 상태:")
    modules_status = get_available_modules()
    for module, available in modules_status.items():
        status = "✅" if available else "❌"
        print(f"  {status} {module}")

    # Lazy 로딩 테스트
    print("\n🚀 Lazy 로딩 테스트:")

    try:
        # 실제 모듈이 있으면 테스트
        if modules_status.get("langchain_core", False):
            print("  ✅ LangChain core 로딩 테스트...")
            # 여기서 실제 import 발생
            lc_version = langchain_core.__version__
            print(f"    LangChain 버전: {lc_version}")
        else:
            print("  ⚠️  LangChain core 미설치 - 로딩 테스트 생략")
    except Exception as e:
        print(f"  ❌ LangChain 테스트 실패: {e}")

    try:
        if modules_status.get("openai", False):
            print("  ✅ OpenAI 로딩 테스트...")
            # 여기서 실제 import 발생
            oa_version = openai.__version__
            print(f"    OpenAI 버전: {oa_version}")
        else:
            print("  ⚠️  OpenAI 미설치 - 로딩 테스트 생략")
    except Exception as e:
        print(f"  ❌ OpenAI 테스트 실패: {e}")

    print("\n🎉 Lazy Import 모듈 테스트 완료!")
    print("💡 실제 사용 시 모듈 접근할 때 로딩됩니다.")
