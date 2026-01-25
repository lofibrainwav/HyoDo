"""
Unit Tests for Phase 5 AI Layer
Tests:
- Domain Models (Validation)
- PII Redactor (Regex Logic)
- RAG Engine (Mock Retrieval)
- Prompt Templates (Formatting)
"""

import pytest
from domain.ai.models import AIRequest
from infrastructure.ai.gateway import ai_gateway
from infrastructure.middleware.pii_redactor import PIIRedactor
from infrastructure.rag.engine import RAGEngine
from pydantic import ValidationError

# --- 1. Domain Model Tests ---


def test_ai_request_validation() -> None:
    """Test AIRequest Pydantic validation."""
    # Valid Request
    req = AIRequest(query="Hello", persona="general")
    assert req.query == "Hello"
    assert req.stream is True

    # Empty Query
    with pytest.raises(ValidationError):
        AIRequest(query="   ")

    # Max Token Overflow
    with pytest.raises(ValidationError):
        AIRequest(query="test", max_tokens=5000)


# --- 2. PII Redactor Tests ---


def test_pii_redaction() -> None:
    """Test Regex-based redaction."""
    text = "Call me at 555-123-4567 or email test@example.com."
    redacted = PIIRedactor.redact(text)

    assert "555-123-4567" not in redacted
    assert "test@example.com" not in redacted
    assert "[PHONE_REDACTED]" in redacted
    assert "[EMAIL_REDACTED]" in redacted


def test_ssn_redaction() -> None:
    text = "My SSN is 123-45-6789."
    redacted = PIIRedactor.redact_query(text)
    assert "123-45-6789" not in redacted
    assert "[SSN_REDACTED]" in redacted


# --- 3. RAG Engine Tests ---


@pytest.mark.asyncio
@pytest.mark.integration
async def test_rag_real_retrieval() -> None:
    """Test RAG Engine real LanceDB connectivity."""
    engine = RAGEngine()

    # Test Identity Query (should hit kingdom_identity table)
    chunks = await engine.retrieve_context("사령관 호칭")

    # Skip if LanceDB table not initialized (CI environment)
    if len(chunks) == 0:
        pytest.skip("LanceDB table 'kingdom_identity' not initialized - skipping in CI")

    assert "사령관" in chunks[0].content or "형님" in chunks[0].content
    assert chunks[0].source == "IDENTITY_CORE"


# --- 4. Prompt Template Tests ---


@pytest.mark.asyncio
async def test_ai_gateway_real_stream() -> None:
    """Test AI Gateway real Ollama streaming."""
    req = AIRequest(query="Hello", persona="developer", stream=True)

    chunks = []
    async for chunk in ai_gateway.generate_stream(req):
        chunks.append(chunk)

    assert len(chunks) > 0
    assert any(len(c) > 0 for c in chunks)
