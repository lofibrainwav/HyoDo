"""
RAG Streaming API Routes - Contract v3 준수
북극성: 스트리밍 중 interrupt → fork → resume 지원
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from AFO.services.rag_streaming_service import RAGStreamingService

router = APIRouter(prefix="/rag", tags=["rag_streaming"])


# Contract v3 모델들
class StreamStartRequest(BaseModel):
    checkpoint_id: str
    fork_name: str
    run_config: dict[str, Any]
    stream: bool = True


class StreamStartResponse(BaseModel):
    run_id: str
    status: str
    diff_summary: str
    stream_url: str


class InterruptRequest(BaseModel):
    run_id: str


class InterruptResponse(BaseModel):
    run_id: str
    status: str
    checkpoint_saved: bool
    last_checkpoint_id: str | None


class ResumeRequest(BaseModel):
    run_id: str


class ResumeResponse(BaseModel):
    run_id: str
    status: str
    stream_url: str


# 서비스 인스턴스
rag_streaming_service = RAGStreamingService()


@router.post("/start", response_model=StreamStartResponse)
async def start_rag_stream(request: StreamStartRequest) -> StreamStartResponse:
    """
    RAG 스트리밍 시작 (Contract v3 Start)
    스트리밍 런 생성 + stream_url 발급
    """
    try:
        return await rag_streaming_service.start_streaming_run(
            checkpoint_id=request.checkpoint_id,
            fork_name=request.fork_name,
            run_config=request.run_config,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스트리밍 시작 실패: {e!s}")


@router.get("/stream")
async def stream_rag_response(run_id: str) -> StreamingResponse:
    """
    RAG 응답 스트리밍 (Contract v3 Stream)
    SSE 이벤트로 청크별 전송
    """
    try:
        return StreamingResponse(
            rag_streaming_service.stream_rag_response(run_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스트리밍 실패: {e!s}")


@router.post("/interrupt", response_model=InterruptResponse)
async def interrupt_rag_stream(request: InterruptRequest) -> InterruptResponse:
    """
    RAG 스트리밍 중단 (Contract v3 Control)
    스트리밍 중단 + 체크포인트 저장
    """
    try:
        return await rag_streaming_service.interrupt_stream(request.run_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"중단 실패: {e!s}")


@router.post("/resume", response_model=ResumeResponse)
async def resume_rag_stream(request: ResumeRequest) -> ResumeResponse:
    """
    RAG 스트리밍 재개 (Contract v3 Control)
    스트리밍 재개 + 새로운 stream_url
    """
    try:
        return await rag_streaming_service.resume_stream(request.run_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"재개 실패: {e!s}")


@router.get("/status/{run_id}")
async def get_rag_stream_status(run_id: str) -> dict[str, Any]:
    """
    RAG 스트리밍 상태 조회
    """
    try:
        return await rag_streaming_service.get_stream_status(run_id)
    except Exception:
        raise HTTPException(status_code=404, detail=f"스트림을 찾을 수 없음: {run_id}")
