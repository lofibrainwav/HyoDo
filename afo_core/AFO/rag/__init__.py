# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO Kingdom: RAG Package
========================
Unified RAG exports using existing DSPy and optimizer modules.
"""

from AFO.rag.dspy_module import DSPyRAGModule, create_dspy_rag
from AFO.rag.optimizer_cli import optimize_rag, run_optimization

__all__ = [
    # DSPy RAG
    "DSPyRAGModule",
    "create_dspy_rag",
    # Optimizer
    "optimize_rag",
    "run_optimization",
]
