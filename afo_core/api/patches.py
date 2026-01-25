"""
API Server Patches - 런타임 호환성 패치

다양한 환경에서의 호환성 문제를 자동으로 해결하는 패치 모듈입니다.
"""

import importlib.util
from pathlib import Path


def patch_typing_inspection_if_needed() -> bool:
    """Self-heal for a known `typing-inspection` startup crash.

    In some environments, `typing_inspection.typing_objects` raises:
    `AttributeError: type object 'tuple' has no attribute '_name'` during import.
    That prevents FastAPI/Pydantic from importing and blocks the API server.

    This patch is safe and idempotent; it only rewrites the installed file when the
    buggy snippet is detected.

    Returns:
        True if patch was applied, False if not needed or failed.
    """
    spec = importlib.util.find_spec("typing_inspection.typing_objects")
    if not spec or not spec.origin:
        return False

    path = Path(spec.origin)
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False

    # Already patched.
    if "alias_name = getattr(alias" in text:
        return False

    needle = "if (te_alias := getattr(typing_extensions, alias._name, None)) is not None:"
    if needle not in text:
        return False

    replacement = (
        "alias_name = getattr(alias, '_name', None) or getattr(alias, '__name__', None)\n"
        "    if not alias_name:\n"
        "        continue\n"
        "    if (te_alias := getattr(typing_extensions, alias_name, None)) is not None:"
    )

    try:
        path.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
        return True
    except Exception:
        return False
