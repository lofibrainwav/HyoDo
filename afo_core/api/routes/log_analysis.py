"""
AFO 왕국 Log Analysis API Router
Phase 43: The Cybernetic Loop (자율 진화의 고리)

로그 분석 시스템을 위한 REST API 엔드포인트들을 제공합니다.
Cybernetic Loop의 핵심 컴포넌트로 Self-Diagnostics와 통합됩니다.
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from AFO.serenity.self_diagnostics import SelfDiagnostics
from AFO.services.log_analysis import LogAnalysisService

logger = logging.getLogger(__name__)

# API Router 생성
router = APIRouter(
    prefix="/logs",
    tags=["log-analysis"],
    responses={404: {"description": "Log analysis endpoint not found"}},
)

# 서비스 인스턴스들
log_service = LogAnalysisService()
diagnostics = SelfDiagnostics()


class LogAnalysisRequest(BaseModel):
    """로그 분석 요청 모델"""

    log_file_path: str = Field(..., description="분석할 로그 파일의 경로")
    output_dir: str | None = Field(None, description="출력 디렉토리 (선택사항)")
    chunk_size: int | None = Field(100, ge=10, le=1000, description="청크 크기")
    enable_diagnostics: bool = Field(True, description="Cybernetic Loop 진단 활성화")

    class Config:
        json_schema_extra = {
            "example": {
                "log_file_path": "/var/log/application.log",
                "output_dir": "analysis_results",
                "chunk_size": 200,
                "enable_diagnostics": True,
            }
        }


class LogAnalysisResponse(BaseModel):
    """로그 분석 응답 모델"""

    request_id: str
    status: str
    pipeline_result: dict[str, Any]
    cybernetic_impact: dict[str, Any] | None = None
    execution_time: float

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "log_analysis_123456",
                "status": "completed",
                "pipeline_result": {
                    "chunking": {"status": "success", "chunks_created": 5},
                    "sequential": {"status": "success"},
                    "plugins": {},
                },
                "cybernetic_impact": {
                    "truth_score_change": -0.15,
                    "pain_detection": True,
                },
                "execution_time": 2.34,
            }
        }


@router.post(
    "/analyze",
    response_model=LogAnalysisResponse,
    summary="로그 파일 분석 실행",
    description="""
    지정된 로그 파일에 대해 완전한 로그 분석 파이프라인을 실행합니다.

    **Cybernetic Loop 통합:**
    - 로그 분석 결과가 Self-Diagnostics에 반영됩니다
    - Critical 로그 감지 시 Truth Score 자동 조정
    - 시스템 건강 상태 실시간 업데이트
    """,
)
async def analyze_logs(
    request: LogAnalysisRequest,
    background_tasks: BackgroundTasks,
    async_execution: bool = Query(False, description="비동기 실행 여부"),
) -> LogAnalysisResponse:
    """
    로그 분석 API 엔드포인트

    Args:
        request: 로그 분석 요청
        background_tasks: FastAPI 백그라운드 태스크
        async_execution: 비동기 실행 모드

    Returns:
        분석 결과 응답
    """
    import time
    import uuid

    request_id = f"log_analysis_{uuid.uuid4().hex[:8]}"
    start_time = time.time()

    logger.info(f"🚀 Starting log analysis request: {request_id}")
    logger.info(f"📁 Target file: {request.log_file_path}")

    try:
        # 로그 파일 존재 확인
        if not Path(request.log_file_path).exists():
            raise HTTPException(
                status_code=404, detail=f"Log file not found: {request.log_file_path}"
            )

        # 서비스 초기화 (커스텀 출력 디렉토리)
        service = LogAnalysisService(output_dir=request.output_dir)

        # Cybernetic Loop: 사전 진단
        pre_diagnostics = None
        if request.enable_diagnostics:
            logger.info("🩺 Running pre-analysis diagnostics")
            pre_diagnostics = await diagnostics.run_full_diagnosis()
            logger.info(f"📊 Pre-analysis Truth Score: {pre_diagnostics['trinity']['truth']:.3f}")

        # 로그 분석 실행
        if async_execution:
            # 비동기 실행: 백그라운드에서 처리
            background_tasks.add_task(_execute_log_analysis_async, service, request, request_id)

            return LogAnalysisResponse(
                request_id=request_id,
                status="accepted",
                pipeline_result={"message": "Analysis started in background"},
                cybernetic_impact=None,
                execution_time=0.0,
            )

        else:
            # 동기 실행: 즉시 처리
            pipeline_result = await _execute_log_analysis_async(service, request, request_id)

            # Cybernetic Loop: 사후 진단
            post_diagnostics = None
            cybernetic_impact = None

            if request.enable_diagnostics and pre_diagnostics:
                logger.info("🩺 Running post-analysis diagnostics")
                post_diagnostics = await diagnostics.run_full_diagnosis()
                logger.info(
                    f"📊 Post-analysis Truth Score: {post_diagnostics['trinity']['truth']:.3f}"
                )

                # Cybernetic Loop 효과 계산
                cybernetic_impact = _calculate_cybernetic_impact(
                    pre_diagnostics, post_diagnostics, pipeline_result
                )

            execution_time = time.time() - start_time

            return LogAnalysisResponse(
                request_id=request_id,
                status="completed",
                pipeline_result=pipeline_result,
                cybernetic_impact=cybernetic_impact,
                execution_time=execution_time,
            )

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"💥 Log analysis failed: {e}")

        raise HTTPException(status_code=500, detail=f"Log analysis failed: {e!s}")


async def _execute_log_analysis_async(
    service: LogAnalysisService, request: LogAnalysisRequest, request_id: str
) -> dict[str, Any]:
    """로그 분석 실행 (비동기)"""
    try:
        logger.info(f"🔍 Executing log analysis pipeline for {request_id}")

        # 파이프라인 실행
        result = service.run_pipeline(request.log_file_path)

        if result["pipeline_status"] == "SUCCESS":
            logger.info(f"✅ Log analysis completed successfully for {request_id}")
        else:
            logger.warning(f"⚠️ Log analysis completed with issues for {request_id}")

        return result

    except Exception as e:
        logger.error(f"💥 Log analysis execution failed for {request_id}: {e}")
        return {"pipeline_status": "FAILED", "error": str(e), "request_id": request_id}


def _calculate_cybernetic_impact(
    pre_diagnostics: dict[str, Any],
    post_diagnostics: dict[str, Any],
    pipeline_result: dict[str, Any],
) -> dict[str, Any]:
    """Cybernetic Loop 효과 계산"""

    pre_truth = pre_diagnostics["trinity"]["truth"]
    post_truth = post_diagnostics["trinity"]["truth"]

    score_change = pre_truth - post_truth
    score_drop_percentage = (score_change / pre_truth) * 100 if pre_truth > 0 else 0

    # 고통 감지: Truth Score 5% 이상 하락 (API 호출용 기준)
    pain_detection = score_drop_percentage >= 5.0

    # 분석 성공
    analysis_success = pipeline_result.get("pipeline_status") == "SUCCESS"

    return {
        "pre_truth_score": pre_truth,
        "post_truth_score": post_truth,
        "score_change": score_change,
        "score_drop_percentage": score_drop_percentage,
        "pain_detection": pain_detection,
        "analysis_success": analysis_success,
        "cybernetic_integrity": pain_detection and analysis_success,
    }


@router.get(
    "/health",
    summary="로그 분석 서비스 건강 상태",
    description="Log Analysis 서비스의 현재 건강 상태를 반환합니다.",
)
async def get_log_analysis_health():
    """로그 분석 서비스 건강 상태 확인"""
    try:
        # 기본 건강 체크
        health_status = {
            "service": "log_analysis",
            "status": "healthy",
            "version": "1.0.0",
            "capabilities": [
                "log_chunking",
                "sequential_analysis",
                "plugin_system",
                "cybernetic_loop",
            ],
        }

        # 추가 상태 정보
        health_status["diagnostics_available"] = True
        health_status["pipeline_ready"] = True

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Log analysis service unhealthy")


@router.get(
    "/diagnostics",
    summary="Cybernetic Loop 진단 상태",
    description="현재 Self-Diagnostics 상태와 Truth Score를 반환합니다.",
)
async def get_cybernetic_diagnostics():
    """Cybernetic Loop 진단 상태 조회"""
    try:
        report = await diagnostics.run_full_diagnosis()

        return {
            "timestamp": report["timestamp"],
            "trinity_scores": report["trinity"],
            "overall_health": report["status"],
            "details": [
                {
                    "lens": detail.lens,
                    "status": detail.status,
                    "score": detail.score,
                    "findings": detail.findings,
                }
                for detail in report["details"]
            ],
        }

    except Exception as e:
        logger.error(f"Diagnostics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve diagnostics")


@router.post(
    "/inject-critical",
    summary="Critical 로그 주입 (테스트용)",
    description="테스트 목적으로 Critical 레벨 로그를 시스템에 주입합니다.",
)
async def inject_critical_logs(
    count: int = Query(1, ge=1, le=10, description="주입할 Critical 로그 개수"),
):
    """Critical 로그 주입 (테스트용)"""
    try:
        # 임시 로그 파일 생성
        temp_log = Path("critical_injection_test.log")

        critical_patterns = [
            "[CRITICAL] Database connection timeout",
            "[CRITICAL] Memory allocation failed",
            "[CRITICAL] Authentication service down",
            "[CRITICAL] File system corruption",
            "[CRITICAL] Network partition detected",
        ]

        with open(temp_log, "w") as f:
            for i in range(count):
                pattern = critical_patterns[i % len(critical_patterns)]
                f.write(f"{pattern} (injected #{i + 1})\n")

        logger.warning(f"💉 Injected {count} critical logs for testing")

        return {
            "status": "injected",
            "log_file": str(temp_log),
            "injected_count": count,
            "message": "Critical logs injected. Run diagnostics to verify Cybernetic Loop.",
        }

    except Exception as e:
        logger.error(f"Critical log injection failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to inject critical logs")
