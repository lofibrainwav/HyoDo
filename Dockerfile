# HyoDo - model-agnostic quality gates for AI-assisted development

FROM python:3.12-slim

LABEL maintainer="AFO Kingdom <afokingdom@example.com>"
LABEL version="4.0.0"
LABEL description="HyoDo - AI Code Quality Automation"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml ./
COPY README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir \
    ruff \
    pyright \
    pytest \
    pydantic \
    typer \
    rich

# Copy application code (public surface only)
COPY scripts/ ./scripts/
COPY hyodo/ ./hyodo/

# Install the package
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 hyodo && chown -R hyodo:hyodo /app
USER hyodo

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import hyodo; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "hyodo.cli.main", "--help"]
