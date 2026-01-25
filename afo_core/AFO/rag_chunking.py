import os


def _enabled() -> bool:
    return os.getenv("AFO_RAG_CHUNK_ENABLED", "0") == "1"


def _chunk_size() -> int:
    try:
        return int(os.getenv("AFO_RAG_CHUNK_SIZE", "500"))
    except Exception:
        return 500


def _overlap() -> int:
    try:
        return int(os.getenv("AFO_RAG_CHUNK_OVERLAP", "75"))
    except Exception:
        return 75


def smart_chunk(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    if not _enabled():
        return [text]

    cs = chunk_size if chunk_size is not None else _chunk_size()
    ov = overlap if overlap is not None else _overlap()
    if cs <= 0:
        return [text]
    if ov < 0:
        ov = 0
    if ov >= cs:
        ov = max(0, cs // 5)

    s = text.strip()
    if len(s) <= cs:
        return [s]

    out: list[str] = []
    i = 0
    while i < len(s):
        j = min(len(s), i + cs)
        out.append(s[i:j])
        if j == len(s):
            break
        i = max(0, j - ov)
    return out
