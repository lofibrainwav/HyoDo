# Trinity Score: 95.0 (Established by Chancellor)
"""
Fast JSON module with ujson fallback to standard json.

OPTIMIZATION: Uses ujson (2-3x faster) when available, falls back to json.
Hot paths should import from this module instead of json directly.

Usage:
    from infrastructure.json_fast import dumps, loads
"""

from typing import Any

try:
    import ujson

    _USE_UJSON = True
except ImportError:
    import json as _json_fallback

    _USE_UJSON = False


def dumps(obj: Any, *, ensure_ascii: bool = False, sort_keys: bool = False, **kwargs: Any) -> str:
    """Fast JSON serialization (ujson when available).

    Args:
        obj: Object to serialize
        ensure_ascii: If True, escape non-ASCII characters
        sort_keys: If True, sort dictionary keys
        **kwargs: Additional arguments (passed to json if ujson unavailable)

    Returns:
        JSON string
    """
    if _USE_UJSON:
        # ujson doesn't support sort_keys directly, but it's faster
        # For cache keys where sort_keys matters, we handle it differently
        if sort_keys:
            # Fall back to stdlib for sorted keys (rare case)
            import json

            return json.dumps(obj, ensure_ascii=ensure_ascii, sort_keys=True)
        return ujson.dumps(obj, ensure_ascii=ensure_ascii)
    return _json_fallback.dumps(obj, ensure_ascii=ensure_ascii, sort_keys=sort_keys, **kwargs)


def loads(s: str | bytes, **kwargs: Any) -> Any:
    """Fast JSON deserialization (ujson when available).

    Args:
        s: JSON string or bytes to parse
        **kwargs: Additional arguments (passed to json if ujson unavailable)

    Returns:
        Parsed Python object
    """
    if _USE_UJSON:
        return ujson.loads(s)
    return _json_fallback.loads(s, **kwargs)
