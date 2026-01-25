"""
Observability Setup - Sentry and OpenTelemetry 초기화

AFO Kingdom API 서버의 모니터링 및 추적 시스템을 설정합니다.
"""

import logging
from typing import TYPE_CHECKING

# Optional Monitoring & Tracing Imports
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None  # type: ignore

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None  # type: ignore
    FastAPIInstrumentor = None  # type: ignore

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


def setup_sentry() -> bool:
    """Initialize Sentry for error tracking and performance monitoring.

    Trinity Score: 善 (Goodness) - 실시간 에러 포착 및 시스템 안정성 강화

    Returns:
        True if Sentry was initialized successfully, False otherwise.
    """
    if not SENTRY_AVAILABLE:
        logger.info("ℹ️ Sentry SDK not available, skipping initialization")
        return False

    try:
        # DSN should be configured via environment or config
        # Using a placeholder for now as per user request
        dsn = "${SENTRY_DSN:-}"

        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            environment="development",
            release="afo-core@1.0.0",
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                StarletteIntegration(),
                LoggingIntegration(level=logging.ERROR, event_level=logging.CRITICAL),
            ],
            send_default_pii=False,
        )
        logger.info("✅ Sentry initialized successfully")
        return True
    except Exception:
        logger.warning("⚠️ Sentry initialization skipped (configuration issue or SDK missing)")
        return False


def setup_opentelemetry() -> bool:
    """Initialize OpenTelemetry (Traces, Logs, Metrics).

    Uses OTLP Exporter (gRPC) for standardized telemetry data transmission.

    Returns:
        True if OpenTelemetry was initialized successfully, False otherwise.
    """
    if not OTEL_AVAILABLE:
        logger.info("ℹ️ OpenTelemetry not available, skipping initialization")
        return False

    try:
        resource = Resource.create(
            attributes={
                "service.name": "afo-core",
                "service.version": "1.0.0",
                "deployment.environment": "dev",
            }
        )

        # Setup Trace Provider
        provider = TracerProvider(resource=resource)
        processor = BatchSpanProcessor(
            OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
        )
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        # Setup Logging
        LoggingInstrumentor().instrument(set_logging_format=True)

        logger.info("✅ OpenTelemetry initialized successfully")
        return True
    except Exception:
        logger.warning("⚠️ OpenTelemetry initialization skipped")
        return False


def instrument_fastapi(app: "FastAPI") -> bool:
    """Instrument FastAPI app with OpenTelemetry.

    Args:
        app: FastAPI application instance

    Returns:
        True if instrumentation was successful, False otherwise.
    """
    if not OTEL_AVAILABLE or FastAPIInstrumentor is None:
        return False

    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("OpenTelemetry FastAPI instrumentation applied")
        return True
    except Exception as e:
        logger.warning(f"Failed to instrument FastAPI: {e}")
        return False
