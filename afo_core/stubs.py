"""Type stubs for AFO Kingdom modules
This file provides minimal type stubs to resolve Pyright import issues
"""


# Stub modules that may not exist but are referenced
class AFO:
    @staticmethod
    def config() -> None:
        return None

    @staticmethod
    def antigravity() -> None:
        return None

    @staticmethod
    def api_wallet() -> None:
        return None

    @staticmethod
    def llm_router() -> None:
        return None

    @staticmethod
    def input_server() -> None:
        return None

    @staticmethod
    def afo_skills_registry() -> None:
        return None

    @staticmethod
    def api_server() -> None:
        return None

    @staticmethod
    def chancellor_graph() -> None:
        return None

    @staticmethod
    def kms() -> None:
        return None

    @staticmethod
    def scholars() -> None:
        return None

    @staticmethod
    def services() -> None:
        return None

    @staticmethod
    def utils() -> None:
        return None

    @staticmethod
    def llms() -> None:
        return None

    @staticmethod
    def domain() -> None:
        return None


# Stub for optional dependencies
try:
    import crewai
except ImportError:
    crewai = None

try:
    import autogen
except ImportError:
    autogen = None

try:
    import docx
except ImportError:
    docx = None
