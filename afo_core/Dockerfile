# ==========================================
# Phase 17: Cloud Ascension - Unified Build
# ==========================================
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies globally
COPY requirements.txt requirements_minimal.txt* ./
RUN pip install --no-cache-dir -r requirements.txt || pip install --no-cache-dir -r requirements_minimal.txt

# Install Playwright browsers (chromium only for size efficiency)
RUN playwright install --with-deps chromium



# Explicit uvicorn installation (RAG service fix)
RUN pip install --no-cache-dir "uvicorn[standard]>=0.31.1"
RUN python -c "import uvicorn; print('uvicorn', uvicorn.__version__)"

# Explicit slowapi installation (Rate limiting - Phase 38 fix)
RUN pip install --no-cache-dir slowapi
RUN python -c "import slowapi; print('slowapi installed successfully')"

# Explicit dspy installation (AI agents framework)
RUN pip install --no-cache-dir dspy
RUN python -c "import dspy; print('dspy installed successfully')"

# Additional required packages
RUN pip install --no-cache-dir psutil loguru neo4j sqlmodel httpx aiohttp
RUN python -c "import psutil, loguru, neo4j, sqlmodel, httpx, aiohttp; print('All additional packages installed')"
# Copy Application Code
COPY . /app/

# Set Environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

ENV HOME=/tmp
ENV PIP_CACHE_DIR=/tmp/pip-cache
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Inject Build Fingerprint
ARG BUILD_VERSION=unknown
ENV BUILD_VERSION=${BUILD_VERSION}
ARG GIT_SHA=unknown
ENV GIT_SHA=${GIT_SHA}

RUN python -m pip install -U pip && python -m pip install --no-cache-dir crewai 'crewai[tools]' autogen-agentchat

# Expose Ports
EXPOSE 8010 8001

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8010/health || exit 1

# Command
CMD ["python", "-m", "uvicorn", "AFO.api_server:app", "--host", "0.0.0.0", "--port", "8010"]
