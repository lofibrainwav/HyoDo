"""
MyGPT 통합용 Pydantic 모델

OpenAI ChatGPT Actions와 jangjungwha.com 간의 데이터 교환을 위한 스펙
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GPTTarget(str, Enum):
    """MyGPT GPT 타겟"""

    JULIE_CPA = "g-p-67e0ae35e0ec81918fecfcf005b8a746"
    JULIE_AUDIT = "julie-audit-gpt"
    JULIE_STRATEGY = "julie-strategy-gpt"


class MyGPTTransferRequest(BaseModel):
    """MyGPT로 컨텍스트 전송 요청"""

    notebook_id: str = Field(..., description="Notebook ID")
    target_gpt_id: str = Field(..., description="Target GPT ID")
    append_mode: bool = Field(default=True, description="기존 내용에 추가할지 여부")
    metadata: dict[str, Any] | None = Field(default=None, description="추가 메타데이터")


class MyGPTTransferResponse(BaseModel):
    """MyGPT 전송 응답"""

    success: bool = Field(..., description="전송 성공 여부")
    message: str = Field(..., description="응답 메시지")
    transfer_id: str = Field(..., description="전송 ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="전송 시간")


class MyGPTStatusResponse(BaseModel):
    """MyGPT 연동 상태 응답"""

    connected: bool = Field(..., description="MyGPT 연결 상태")
    gpt_configured: bool = Field(..., description="GPT 설정 여부")
    last_sync: datetime | None = Field(default=None, description="마지막 동기화 시간")
    active_contexts: int = Field(default=0, description="활성 컨텍스트 수")


class MyGPTSyncRequest(BaseModel):
    """양방향 동기화 요청"""

    force: bool = Field(default=False, description="강제 동기화")
    sync_type: str = Field(default="auto", description="동기화 타입")


class MyGPTSyncResponse(BaseModel):
    """양방향 동기화 응답"""

    sync_success: bool = Field(..., description="동기화 성공 여부")
    contexts_synced: int = Field(..., description="동기화된 컨텍스트 수")
    last_sync_time: datetime = Field(default_factory=datetime.utcnow, description="동기화 시간")
    sync_type: str = Field(..., description="동기화 타입")


class MyGPTContextItem(BaseModel):
    """MyGPT 컨텍스트 아이템"""

    id: str = Field(..., description="컨텍스트 ID")
    title: str = Field(..., description="제목")
    tags: list[str] = Field(default_factory=list, description="태그")
    content_preview: str = Field(..., description="내용 미리보기 (100자)")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")


class MyGPTContextsResponse(BaseModel):
    """MyGPT 컨텍스트 목록 응답"""

    contexts: list[MyGPTContextItem] = Field(..., description="컨텍스트 목록")
    total: int = Field(..., description="전체 개수")
    page: int = Field(default=1, description="페이지 번호")


class MyGPTConfig(BaseModel):
    """MyGPT 설정"""

    gpt_id: str = Field(..., description="GPT ID")
    gpt_name: str = Field(..., description="GPT 이름")
    api_key: str = Field(..., description="API 키")
    webhook_url: str | None = Field(default=None, description="웹훅 URL")
    enabled: bool = Field(default=True, description="활성화 여부")


class MyGPTHandoffRequest(BaseModel):
    """자동 핸드오프 요청"""

    project_id: str = Field(..., description="프로젝트 ID")
    context_summary: str = Field(..., description="컨텍스트 요약")
    priority: str = Field(default="normal", description="우선순위")
    metadata: dict[str, Any] | None = Field(default=None, description="추가 메타데이터")


class MyGPTHandoffResponse(BaseModel):
    """자동 핸드오프 응답"""

    handoff_success: bool = Field(..., description="핸드오프 성공 여부")
    handoff_id: str = Field(..., description="핸드오프 ID")
    target_gpt: str = Field(..., description="타겟 GPT")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="핸드오프 시간")


class MyGPTAutoHandoffConfig(BaseModel):
    """자동 핸드오프 설정"""

    enabled: bool = Field(default=False, description="자동 핸드오프 활성화 여부")
    trigger_keywords: list[str] = Field(default_factory=list, description="핸드오프 트리거 키워드")
    context_window: int = Field(default=10000, description="컨텍스트 윈도우 토큰 수")
    auto_sync: bool = Field(default=True, description="자동 동기화 여부")
