# HyoDo - model-agnostic quality gates for AI-assisted development

FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md requirements.runtime.txt ./
COPY hyodo/ ./hyodo/
COPY schemas/ ./schemas/
COPY LICENSE CHANGELOG.md VERSION SECURITY.md CONTRIBUTING.md CODE_OF_CONDUCT.md ./

# Resolve the lock-derived runtime set before building the application wheel.
RUN python -m pip install --no-cache-dir --no-compile -r requirements.runtime.txt \
    && python -m pip wheel --no-cache-dir --no-deps --wheel-dir /wheels .

FROM python:3.12-slim

LABEL maintainer="AFO Kingdom"
LABEL version="4.19.6"
LABEL description="HyoDo - AI Code Quality Automation"

WORKDIR /app
COPY --from=builder /build/requirements.runtime.txt ./
COPY --from=builder /wheels/ ./

# The final image receives only exact runtime dependencies and the built wheel.
RUN python -m pip install --no-cache-dir --no-compile -r requirements.runtime.txt \
    && python -m pip install --no-cache-dir --no-compile --no-deps /app/hyodo-*.whl \
    && python -m pip uninstall -y pip setuptools wheel >/dev/null 2>&1 || true

RUN useradd -m -u 1000 hyodo && chown -R hyodo:hyodo /app
USER hyodo

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import hyodo; print('OK')" || exit 1

CMD ["python", "-m", "hyodo.cli.main", "--help"]
