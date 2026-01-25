# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO Input Server (AFO/input_server.py)

FastAPI server for processing environment variable input.
"""

import re

from input_server.core import app

# Service keyword mapping
SERVICE_KEYWORDS: dict[str, str] = {
    "openai": "openai",
    "anthropic": "anthropic",
    "github": "github",
    "n8n": "n8n",
    "claude": "anthropic",
    "gpt": "openai",
}


def detect_service(key: str) -> str:
    """Detect service from key name."""
    key_lower = key.lower()
    for keyword, service in SERVICE_KEYWORDS.items():
        if keyword in key_lower:
            return service
    return ""


def parse_env_text(text: str) -> list[tuple[str, str, str]]:
    """Parse environment variable text into (key, value, service) tuples."""
    results: list[tuple[str, str, str]] = []

    for line in text.strip().split("\n"):
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("#"):
            continue

        # Try various formats
        # Format: KEY=value or KEY: value or "KEY": "value" or KEY "value"
        match = re.match(
            r'^["\']?(\w+)["\']?\s*[=:]\s*["\']?([^"\']+)["\']?$',
            line,
        )
        if not match:
            # Try KEY "value" format
            match = re.match(r'^["\']?(\w+)["\']?\s+["\']?([^"\']+)["\']?$', line)

        if match:
            key = match.group(1)
            value = match.group(2).strip().strip("\"'")
            service = detect_service(key)
            results.append((key, value, service))

    return results


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "organ": "胃 (Stomach)",
        "service": "AFO Input Server",
    }


@app.post("/parse")
async def parse_input(text: str) -> dict[str, list[tuple[str, str, str]]]:
    """Parse environment text."""
    parsed = parse_env_text(text)
    return {"parsed": parsed}


__all__ = ["app", "parse_env_text", "detect_service"]
