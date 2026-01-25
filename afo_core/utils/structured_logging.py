# Trinity Score: 90.0 (Established by Chancellor)
import json
import logging
import sys
from datetime import UTC, datetime

# Configure logger locally to avoid circular imports
logger = logging.getLogger(__name__)


class RedisLogPublisher:
    """
    [Serenity: 孝] Redis Pub/Sub Publisher for Real-time Logs.
    Eliminates friction by streaming thoughts directly to the Commander.
    """

    CHANNEL = "kingdom:logs:stream"

    def __init__(self) -> None:
        self.redis = None
        try:
            from AFO.utils.cache_utils import cache

            self.redis = cache.redis if cache.enabled else None
        except ImportError:
            pass

    def publish(self, message: str, level: str = "INFO") -> None:
        """Publish log message to Redis Channel"""
        if not self.redis:
            # Fallback to stdout if Redis is down
            print(f"[Fallback Log] {message}")
            return

        payload = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "source": "Chancellor",
        }
        try:
            self.redis.publish(self.CHANNEL, json.dumps(payload))
        except Exception as e:
            print(f"⚠️ Redis Publish Failed: {e}")


# Global Publisher Instance
_publisher = RedisLogPublisher()


def log_sse(message: str) -> None:
    """
    Log message to Redis Pub/Sub (Primary) and Stdout (Secondary).
    This fulfills the [Serenity] requirement of "Zero Friction Observability".

    Args:
        message: Message to stream
    """
    # 1. Stdout for immediate terminal feedback (Backup)
    timestamp = datetime.now(UTC).isoformat()
    print(f"[SSE] {timestamp} - {message}")
    sys.stdout.flush()

    # 2. Redis Pub/Sub for Dashboard Streaming (Primary)
    _publisher.publish(message)
