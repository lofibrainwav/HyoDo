import hashlib
import os
from typing import Any
from unittest.mock import patch

from AFO.rag_flag import determine_rag_mode


def _seed_bucket(seed: str) -> int:
    h = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(h, 16) % 100


def test_kill_switch_always_wins_over_forced_on() -> None:
    headers = {"X-AFO-RAG": "1", "X-AFO-CLIENT-ID": "u1"}
    env = {
        "AFO_RAG_KILL_SWITCH": "1",
        "AFO_RAG_FLAG_ENABLED": "1",
        "AFO_RAG_ROLLOUT_ENABLED": "1",
        "AFO_RAG_ROLLOUT_PERCENT": "100",
    }
    with patch.dict(os.environ, env, clear=False):
        out = determine_rag_mode(headers)
        assert out["mode"] == "killed"
        assert out["applied"] is False


def test_header_forced_off_beats_flag_and_gradual() -> None:
    headers = {"X-AFO-RAG": "0", "X-AFO-CLIENT-ID": "u1"}
    env = {
        "AFO_RAG_KILL_SWITCH": "0",
        "AFO_RAG_FLAG_ENABLED": "1",
        "AFO_RAG_ROLLOUT_ENABLED": "1",
        "AFO_RAG_ROLLOUT_PERCENT": "100",
    }
    with patch.dict(os.environ, env, clear=False):
        out = determine_rag_mode(headers)
        assert out["mode"] == "forced_off"
        assert out["applied"] is False


def test_header_forced_on_beats_everything_except_kill() -> None:
    headers = {"X-AFO-RAG": "1", "X-AFO-CLIENT-ID": "u1"}
    env = {
        "AFO_RAG_KILL_SWITCH": "0",
        "AFO_RAG_FLAG_ENABLED": "0",
        "AFO_RAG_ROLLOUT_ENABLED": "0",
        "AFO_RAG_ROLLOUT_PERCENT": "0",
    }
    with patch.dict(os.environ, env, clear=False):
        out = determine_rag_mode(headers)
        assert out["mode"] == "forced_on"
        assert out["applied"] is True


def test_flag_beats_gradual() -> None:
    headers = {"X-AFO-CLIENT-ID": "u1"}
    env = {
        "AFO_RAG_KILL_SWITCH": "0",
        "AFO_RAG_FLAG_ENABLED": "1",
        "AFO_RAG_ROLLOUT_ENABLED": "1",
        "AFO_RAG_ROLLOUT_PERCENT": "0",
    }
    with patch.dict(os.environ, env, clear=False):
        out = determine_rag_mode(headers)
        assert out["mode"] == "flag"
        assert out["applied"] is True


def test_gradual_respects_percent_and_is_stable_for_same_seed() -> None:
    seed = "stable-user-123"
    headers = {"X-AFO-CLIENT-ID": seed}

    b = _seed_bucket(seed)

    env_on = {
        "AFO_RAG_KILL_SWITCH": "0",
        "AFO_RAG_FLAG_ENABLED": "0",
        "AFO_RAG_ROLLOUT_ENABLED": "1",
        "AFO_RAG_ROLLOUT_PERCENT": str(b + 1 if b < 99 else 100),
    }
    with patch.dict(os.environ, env_on, clear=False):
        out1 = determine_rag_mode(headers)
        out2 = determine_rag_mode(headers)
        assert out1["mode"] == "gradual"
        assert out1["applied"] is True
        assert out2["applied"] is True

    env_off = {
        "AFO_RAG_KILL_SWITCH": "0",
        "AFO_RAG_FLAG_ENABLED": "0",
        "AFO_RAG_ROLLOUT_ENABLED": "1",
        "AFO_RAG_ROLLOUT_PERCENT": str(b),
    }
    with patch.dict(os.environ, env_off, clear=False):
        out3 = determine_rag_mode(headers)
        out4 = determine_rag_mode(headers)
        assert out3["mode"] == "gradual"
        assert out3["applied"] is False
        assert out4["applied"] is False


def test_gradual_disabled_means_shadow_only() -> None:
    headers = {"X-AFO-CLIENT-ID": "u1"}
    env = {
        "AFO_RAG_KILL_SWITCH": "0",
        "AFO_RAG_FLAG_ENABLED": "0",
        "AFO_RAG_ROLLOUT_ENABLED": "0",
        "AFO_RAG_ROLLOUT_PERCENT": "100",
    }
    with patch.dict(os.environ, env, clear=False):
        out = determine_rag_mode(headers)
        assert out["mode"] == "shadow_only"
        assert out["applied"] is False
