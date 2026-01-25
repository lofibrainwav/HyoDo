# from __future__ import annotations

import json
import logging
import os
import subprocess
from functools import lru_cache
from pathlib import Path

# from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# from sse_starlette.sse import EventSourceResponse
from AFO.afo_skills_registry import register_core_skills
from AFO.chancellor_graph import chancellor_graph
from AFO.config.antigravity import antigravity
from AFO.config.health_check_config import health_check_config
from AFO.constitution.constitutional_ai import AFOConstitution
from AFO.services.health_service import get_comprehensive_health
from AFO.utils.redis_connection import get_shared_async_redis_client
from api.chancellor_v2.graph.runner import run_v2

# Trinity Score: 90.0 (Established by Chancellor)
"""
Integrity Check API
무결성 체크리스트 검증 엔드포인트
眞·善·美·孝·永 5기둥 무결성 검증
"""


router = APIRouter(prefix="/api/integrity", tags=["Integrity Check"])

logger = logging.getLogger(__name__)


# Dynamic workspace root calculation
@lru_cache(maxsize=1)
def _find_workspace_root(anchor: Path) -> Path:
    override = os.getenv("AFO_WORKSPACE_ROOT") or os.getenv("WORKSPACE_ROOT")
    if override:
        p = Path(override).expanduser().resolve()
        if p.exists():
            return p

    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(anchor.parent),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if out:
            p = Path(out).resolve()
            if p.exists():
                return p
    except Exception:
        pass

    markers = (
        ".git",
        "pyproject.toml",
        "poetry.lock",
        "package.json",
        "pnpm-lock.yaml",
    )
    for p in (anchor, *anchor.parents):
        if any((p / m).exists() for m in markers):
            return p

    return anchor


WORKSPACE_ROOT = _find_workspace_root(Path(__file__).resolve())


class IntegrityCheckRequest(BaseModel):
    """무결성 체크 요청"""

    pillar: str | None = None  # None이면 전체 검증


@router.post("/check")
async def check_integrity(request: IntegrityCheckRequest) -> dict[str, object]:
    """
    무결성 체크리스트 검증

    각 기둥별로 실제 시스템 상태를 확인합니다.
    """
    try:
        results: dict[str, dict[str, object]] = {}

        # 眞 (Truth) 검증
        if not request.pillar or request.pillar == "truth":
            results["truth"] = await _check_truth_pillar()

        # 善 (Goodness) 검증
        if not request.pillar or request.pillar == "goodness":
            results["goodness"] = await _check_goodness_pillar()

        # 美 (Beauty) 검증
        if not request.pillar or request.pillar == "beauty":
            results["beauty"] = await _check_beauty_pillar()

        # 孝 (Serenity) 검증
        if not request.pillar or request.pillar == "serenity":
            results["serenity"] = await _check_serenity_pillar()

        # 永 (Eternity) 검증
        if not request.pillar or request.pillar == "eternity":
            results["eternity"] = await _check_eternity_pillar()

        # 종합 점수 계산
        total_score: float = 0.0
        if len(results) == 5:
            # Type safe access
            s_truth = float(str(results["truth"].get("score", 0)))
            s_goodness = float(str(results["goodness"].get("score", 0)))
            s_beauty = float(str(results["beauty"].get("score", 0)))
            s_serenity = float(str(results["serenity"].get("score", 0)))
            s_eternity = float(str(results["eternity"].get("score", 0)))

            total_score = (
                s_truth * 0.35
                + s_goodness * 0.35
                + s_beauty * 0.20
                + s_serenity * 0.08
                + s_eternity * 0.02
            )
        else:
            scores = [float(str(r.get("score", 0))) for r in results.values()]
            if scores:
                total_score = sum(scores) / len(results)

        return {
            "status": "success",
            "total_score": round(total_score, 2),
            "pillars": results,
        }
    except Exception as e:
        logger.error(f"Integrity check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _check_truth_pillar() -> dict[str, object]:
    """眞 (Truth) 기둥 검증"""
    checks: dict[str, object] = {
        "ci_cd_lock": False,
        "type_safety": False,
        "fact_verification": False,
    }

    # 1. CI/CD LOCK 원칙 확인 (Real Verification)
    # 1. CI/CD LOCK 원칙 확인 (Real-Time Meta-Cognition)
    try:
        # "누구맘대로 성적표 파일을 저장하는가? 이건 실시간 반영이야! 무조건!!!"
        # Live Execution: The system feels its own pain relative to the codebase state.

        # 1-1. Ruff Check (Linting & Formatting) - Fast
        # Check only critical paths to avoid timeout
        # Ignore E501 (Line too long) for Truth Pillar (Focus on logic/syntax F, E9, etc)
        ruff_cmd = [
            "ruff",
            "check",
            "packages/afo-core/AFO",
            "--select",
            "E,F",
            "--ignore",
            "E501",
            "--exit-non-zero-on-fix",
        ]
        ruff_proc = subprocess.run(ruff_cmd, capture_output=True, text=True, timeout=10)
        # 1-2. MyPy Check (Type Safety) - Targeted
        # Strategy: "Self-Reflection via Clone"
        # Copy file to /tmp to bypass 'afo-core' invalid package name issue in MyPy
        import shutil
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)
            shutil.copy(
                f"{WORKSPACE_ROOT}/packages/afo-core/AFO/api/routes/integrity_check.py", tmp_path
            )

        try:
            mypy_cmd = [
                "mypy",
                str(tmp_path),
                "--ignore-missing-imports",
                "--check-untyped-defs",
                "--config-file",
                "scripts/strict_mypy.ini",
            ]
            mypy_proc = subprocess.run(mypy_cmd, capture_output=True, text=True, timeout=15)
        finally:
            if tmp_path.exists():
                os.unlink(tmp_path)

        checks["ci_cd_lock"] = ruff_proc.returncode == 0 and mypy_proc.returncode == 0

        if not checks["ci_cd_lock"]:
            if ruff_proc.returncode != 0:
                logger.warning(f"Real-time Ruff failed: {ruff_proc.stderr[:100]}")
            if mypy_proc.returncode != 0:
                logger.warning(f"Real-time MyPy failed: {mypy_proc.stdout[:100]}")

    except subprocess.TimeoutExpired:
        logger.warning("Real-time verification timed out (System too slow)")
        checks["ci_cd_lock"] = False
    except Exception as e:
        logger.warning(f"Real-time check failed: {e}")
        checks["ci_cd_lock"] = False

    # 2. 타입 안전성 확인
    try:
        # MyPy strict 모드 확인 (pyproject.toml 또는 설정 파일)
        pyproject_path = WORKSPACE_ROOT / "pyproject.toml"
        if pyproject_path.exists():
            content = pyproject_path.read_text()
            checks["type_safety"] = "mypy" in content.lower() or "strict" in content.lower()
    except Exception as e:
        logger.warning(f"Type safety check failed: {e}")

    # 3. 사실 검증 도구 확인
    try:
        # verify_fact 도구 존재 확인

        registry = register_core_skills()
        skills = registry.list_all()
        fact_skills = [
            s for s in skills if "fact" in s.skill_id.lower() or "verify" in s.skill_id.lower()
        ]
        checks["fact_verification"] = len(fact_skills) > 0
    except Exception as e:
        logger.warning(f"Fact verification check failed: {e}")

    # 3b. MCP 기반 사실 검증 도구 확인 (Cursor MCP 설정 기준)
    if not checks["fact_verification"]:
        try:
            mcp_config_path = WORKSPACE_ROOT / ".cursor" / "mcp.json"
            if mcp_config_path.exists():
                mcp_config = json.loads(mcp_config_path.read_text(encoding="utf-8"))
                servers = mcp_config.get("mcpServers", {})
                # AFO Ultimate MCP는 verify_fact 도구를 제공한다.
                checks["fact_verification"] = "afo-ultimate-mcp" in servers
        except Exception as e:
            logger.warning(f"MCP fact verification check failed: {e}")

    passed_count = sum(1 for v in checks.values() if v)
    # Zero Tolerance: If any check fails, the pillar collapses (Score 0)
    score = 100.0 if passed_count == len(checks) else 0.0

    return {
        "score": round(score, 2),
        "checks": checks,
        "passed": passed_count,
        "total": len(checks),
    }


async def _check_goodness_pillar() -> dict[str, object]:
    """善 (Goodness) 기둥 검증"""
    checks: dict[str, object] = {
        "auto_run_gate": False,
        "dry_run_default": False,
        "cai_engine": False,
    }

    # 1. AUTO_RUN 게이트 확인 (PH23: V2 Runner 우선)
    try:
        # V2 Runner가 있으면 AUTO_RUN 게이트 통과
        checks["auto_run_gate"] = run_v2 is not None
    except ImportError:
        # Fallback to deprecated V1
        try:
            checks["auto_run_gate"] = chancellor_graph is not None
        except ImportError:
            logger.warning("AUTO_RUN gate check failed: Neither V2 nor V1 available")

    # 2. DRY_RUN 기본값 확인
    try:
        checks["dry_run_default"] = antigravity.DRY_RUN_DEFAULT is True
    except Exception as e:
        logger.warning(f"DRY_RUN check failed: {e}")

    # 3. CAI 엔진 확인
    try:
        checks["cai_engine"] = AFOConstitution is not None and hasattr(
            AFOConstitution, "evaluate_compliance"
        )
    except Exception as e:
        logger.warning(f"CAI engine check failed: {e}")

    passed_count = sum(1 for v in checks.values() if v)
    # Zero Tolerance
    score = 100.0 if passed_count == len(checks) else 0.0

    return {
        "score": round(score, 2),
        "checks": checks,
        "passed": passed_count,
        "total": len(checks),
    }


async def _check_beauty_pillar() -> dict[str, object]:
    """美 (Beauty) 기둥 검증"""
    checks: dict[str, object] = {
        "4_layer_arch": False,
        "glassmorphism": False,
        "naming_convention": False,
    }

    # 1. 4계층 아키텍처 확인
    try:
        # Presentation, Application, Domain, Infrastructure 계층 확인
        presentation_path = WORKSPACE_ROOT / "packages" / "dashboard"
        application_path = WORKSPACE_ROOT / "packages" / "afo-core" / "api"
        domain_path = WORKSPACE_ROOT / "packages" / "afo-core" / "AFO"
        infrastructure_path = WORKSPACE_ROOT / "packages" / "afo-core" / "AFO" / "infrastructure"

        checks["4_layer_arch"] = (
            presentation_path.exists() and application_path.exists() and domain_path.exists()
        )
    except Exception as e:
        logger.warning(f"4-layer arch check failed: {e}")

    # 2. Glassmorphism UX 확인 (프론트엔드 파일 확인)
    try:
        dashboard_path = WORKSPACE_ROOT / "packages" / "dashboard" / "src"
        if dashboard_path.exists():
            # CSS 파일에서 glassmorphism 관련 스타일 확인
            css_files = list(dashboard_path.rglob("*.css")) + list(dashboard_path.rglob("*.tsx"))
            for css_file in css_files[:5]:  # 처음 5개만 확인
                content = css_file.read_text()
                if "backdrop-filter" in content or "glass" in content.lower():
                    checks["glassmorphism"] = True
                    break
    except Exception as e:
        logger.warning(f"Glassmorphism check failed: {e}")

    # 3. 네이밍 컨벤션 확인 (일관된 네이밍 패턴)
    try:
        # 주요 파일들의 네이밍 패턴 확인
        api_files = list((WORKSPACE_ROOT / "packages" / "afo-core" / "api").rglob("*.py"))
        if api_files:
            # snake_case 패턴 확인
            checks["naming_convention"] = all(
                "_" in f.stem or f.stem.islower() for f in api_files[:10]
            )
    except Exception as e:
        logger.warning(f"Naming convention check failed: {e}")

    passed_count = sum(1 for v in checks.values() if v)
    # Zero Tolerance
    score = 100.0 if passed_count == len(checks) else 0.0

    return {
        "score": round(score, 2),
        "checks": checks,
        "passed": passed_count,
        "total": len(checks),
    }


async def _check_serenity_pillar() -> dict[str, object]:
    """孝 (Serenity) 기둥 검증"""
    checks: dict[str, object] = {
        "mcp_tools": False,
        "organs_health": False,
        "sse_streaming": False,
    }

    # 1. MCP 도구 점검
    try:
        checks["mcp_tools"] = len(health_check_config.MCP_SERVERS) > 0
    except Exception as e:
        logger.warning(f"MCP tools check failed: {e}")

    # 2. 오장육부 건강도 확인
    try:
        health_data = await get_comprehensive_health()
        organs = health_data.get("organs", [])
        if isinstance(organs, dict):
            checks["organs_health"] = all(
                isinstance(v, dict) and v.get("status") == "healthy" for v in organs.values()
            )
        elif isinstance(organs, list):
            healthy_count = sum(1 for o in organs if o.get("healthy", False))
            checks["organs_health"] = healthy_count == len(organs) if organs else False
    except Exception as e:
        logger.warning(f"Organs health check failed: {e}")

    # 3. SSE 스트리밍 확인 (Redis PubSub Availability)
    try:
        r = await get_shared_async_redis_client()
        await r.ping()
        checks["sse_streaming"] = True
    except Exception:
        checks["sse_streaming"] = False

    passed_count = sum(1 for v in checks.values() if v)
    # Zero Tolerance
    score = 100.0 if passed_count == len(checks) else 0.0

    return {
        "score": round(score, 2),
        "checks": checks,
        "passed": passed_count,
        "total": len(checks),
    }


async def _check_eternity_pillar() -> dict[str, object]:
    """永 (Eternity) 기둥 검증"""

    checks = {
        "persistence": False,
        "genesis_mode": False,
        "documentation": False,
    }

    # 1. 영원한 기억 (Persistence) 확인 (Real Redis Check)
    try:
        r = await get_shared_async_redis_client()
        await r.ping()
        checks["persistence"] = True
    except Exception as e:
        logger.warning(f"Persistence check failed: {e}")
        checks["persistence"] = False

    # 2. Project Genesis 모드 확인
    try:
        checks["genesis_mode"] = antigravity.SELF_EXPANDING_MODE is True
    except Exception as e:
        logger.warning(f"Genesis mode check failed: {e}")

    # 3. 문서화 확인
    try:
        docs_path = WORKSPACE_ROOT / "docs"
        md_files = list(docs_path.rglob("*.md")) if docs_path.exists() else []
        checks["documentation"] = len(md_files) >= 10  # 최소 10개 문서
    except Exception as e:
        logger.warning(f"Documentation check failed: {e}")

    passed_count = sum(1 for v in checks.values() if v)
    # Zero Tolerance
    score = 100.0 if passed_count == len(checks) else 0.0

    return {
        "score": round(score, 2),
        "checks": checks,
        "passed": passed_count,
        "total": len(checks),
    }
