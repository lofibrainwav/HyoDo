"""Tax Document Classifier - Refactored Wrapper.

Original code moved to: AFO/tax_classification/
"""

from .tax_classification import (
    TaxDocumentClassifier,
)

tax_document_classifier = TaxDocumentClassifier()


def classify_tax_document(path: str) -> None:
    # Wrapper implementation
    return {}


__all__ = [
    "TaxDocumentClassifier",
    "tax_document_classifier",
    "classify_tax_document",
]
