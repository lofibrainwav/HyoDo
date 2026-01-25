"""
Julie CPA AI 에이전트 군단 로그 스키마
TICKET-043 Phase 2: IRS 모니터링 강화

JULIE_CPA_2_010126.md 기반 로그 스키마 구현:
- julie_logs 테이블: AI 에이전트 군단 작업 로그
- Trinity Score 기반 로깅
- Evidence Bundle 연동
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# 데이터베이스 파일 절대 경로 계산 (MCP 서버에서도 작동하도록)
_DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "julie_logs.db"
_DB_URL = os.environ.get("JULIE_DB_URL", f"sqlite:///{_DEFAULT_DB_PATH}")
from sqlalchemy import Column, DateTime, Float, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class JulieLogEntry(BaseModel):
    """Julie CPA 로그 엔트리 (JULIE_CPA_2_010126.md 기반)"""

    log_id: str = Field(..., description="고유 식별자 (UUID)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="생성 시각")
    agent: str = Field(..., description="Associate/Manager/Auditor")
    action: str = Field(..., description="데이터 수집/점검/판정")
    input_hash: str = Field(..., description="입력 데이터 SHA256")
    output_hash: str = Field(..., description="산출물 SHA256")
    evidence_id: str = Field(..., description="Evidence Bundle 링크")
    trinity_score: float = Field(..., description="眞善美孝永 점수")
    confidence_score: float = Field(default=0.0, description="AI 판정 신뢰도")
    impact_level: str = Field(default="medium", description="Critical/High/Medium")
    source_url: str = Field(default="", description="IRS/FTB 소스 URL")
    metacognition_insights: dict[str, Any] = Field(
        default_factory=dict, description="메타인지 검증 결과"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class JulieLogTable(Base):
    """Julie CPA 로그 데이터베이스 테이블"""

    __tablename__ = "julie_logs"

    log_id = Column(String(36), primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now(UTC), index=True)
    agent = Column(String(20), index=True)  # Associate/Manager/Auditor
    action = Column(String(100))
    input_hash = Column(String(64), index=True)
    output_hash = Column(String(64), index=True)
    evidence_id = Column(String(36), index=True)
    trinity_score = Column(Float)
    confidence_score = Column(Float, default=0.0)
    impact_level = Column(String(10), default="medium")
    source_url = Column(Text)
    metacognition_insights = Column(Text)  # JSON string

    def __repr__(self) -> None:
        return f"<JulieLog(log_id='{self.log_id}', agent='{self.agent}', action='{self.action}')>"


class JulieLogManager:
    """Julie CPA 로그 관리자"""

    def __init__(self, database_url: str | None = None) -> None:
        database_url = database_url or _DB_URL
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def log_agent_action(self, log_entry: JulieLogEntry) -> bool:
        """AI 에이전트 액션 로깅"""
        try:
            db = self.SessionLocal()
            db_log = JulieLogTable(
                log_id=log_entry.log_id,
                timestamp=log_entry.timestamp,
                agent=log_entry.agent,
                action=log_entry.action,
                input_hash=log_entry.input_hash,
                output_hash=log_entry.output_hash,
                evidence_id=log_entry.evidence_id,
                trinity_score=log_entry.trinity_score,
                confidence_score=log_entry.confidence_score,
                impact_level=log_entry.impact_level,
                source_url=log_entry.source_url,
                metacognition_insights=json.dumps(log_entry.metacognition_insights),
            )
            db.add(db_log)
            db.commit()
            return True
        except Exception as e:
            print(f"로그 저장 실패: {e}")
            return False
        finally:
            db.close()

    def get_logs_by_agent(self, agent: str, limit: int = 100) -> list[JulieLogEntry]:
        """특정 에이전트 로그 조회"""
        try:
            db = self.SessionLocal()
            logs = (
                db.query(JulieLogTable)
                .filter(JulieLogTable.agent == agent)
                .order_by(JulieLogTable.timestamp.desc())
                .limit(limit)
                .all()
            )

            return [self._db_to_entry(log) for log in logs]
        finally:
            db.close()

    def get_logs_by_evidence(self, evidence_id: str) -> list[JulieLogEntry]:
        """특정 Evidence Bundle 관련 로그 조회"""
        try:
            db = self.SessionLocal()
            logs = (
                db.query(JulieLogTable)
                .filter(JulieLogTable.evidence_id == evidence_id)
                .order_by(JulieLogTable.timestamp.asc())
                .all()
            )

            return [self._db_to_entry(log) for log in logs]
        finally:
            db.close()

    def get_recent_logs(self, hours: int = 24) -> list[JulieLogEntry]:
        """최근 로그 조회"""
        try:
            db = self.SessionLocal()
            cutoff = datetime.now(UTC).replace(hour=datetime.now(UTC).hour - hours)
            logs = (
                db.query(JulieLogTable)
                .filter(JulieLogTable.timestamp >= cutoff)
                .order_by(JulieLogTable.timestamp.desc())
                .all()
            )

            return [self._db_to_entry(log) for log in logs]
        finally:
            db.close()

    def get_trinity_score_stats(self) -> dict[str, Any]:
        """Trinity Score 통계"""
        try:
            db = self.SessionLocal()
            result = (
                db.query(
                    JulieLogTable.agent,
                    db.func.avg(JulieLogTable.trinity_score).label("avg_score"),
                    db.func.count(JulieLogTable.log_id).label("count"),
                )
                .group_by(JulieLogTable.agent)
                .all()
            )

            stats = {}
            for row in result:
                stats[row.agent] = {
                    "average_trinity_score": float(row.avg_score),
                    "total_logs": row.count,
                }
            return stats
        finally:
            db.close()

    def _db_to_entry(self, db_log: JulieLogTable) -> JulieLogEntry:
        """데이터베이스 로그를 Pydantic 모델로 변환"""
        return JulieLogEntry(
            log_id=db_log.log_id,
            timestamp=db_log.timestamp,
            agent=db_log.agent,
            action=db_log.action,
            input_hash=db_log.input_hash,
            output_hash=db_log.output_hash,
            evidence_id=db_log.evidence_id,
            trinity_score=db_log.trinity_score,
            confidence_score=db_log.confidence_score,
            impact_level=db_log.impact_level,
            source_url=db_log.source_url,
            metacognition_insights=json.loads(db_log.metacognition_insights or "{}"),
        )


# 글로벌 로그 관리자 인스턴스
julie_log_manager = JulieLogManager()


def log_associate_action(
    input_data: dict[str, Any], output_data: dict[str, Any], evidence_id: str
) -> bool:
    """Associate 레벨 액션 로깅"""
    import hashlib

    input_str = json.dumps(input_data, sort_keys=True)
    output_str = json.dumps(output_data, sort_keys=True)

    log_entry = JulieLogEntry(
        log_id=f"assoc_{evidence_id[:8]}",
        agent="Associate",
        action="데이터 수집 및 초안 작성",
        input_hash=hashlib.sha256(input_str.encode()).hexdigest(),
        output_hash=hashlib.sha256(output_str.encode()).hexdigest(),
        evidence_id=evidence_id,
        trinity_score=output_data.get("confidence_score", 0.85),
        confidence_score=output_data.get("confidence_score", 0.85),
        impact_level="low",
        metacognition_insights={
            "data_quality": "structured",
            "evidence_links": len(output_data.get("evidence_list", [])),
        },
    )

    return julie_log_manager.log_agent_action(log_entry)


def log_manager_action(
    input_data: dict[str, Any], output_data: dict[str, Any], evidence_id: str
) -> bool:
    """Manager 레벨 액션 로깅"""
    import hashlib

    input_str = json.dumps(input_data, sort_keys=True)
    output_str = json.dumps(output_data, sort_keys=True)

    quality_gate = output_data.get("quality_gate", {})
    risk_score = output_data.get("risk_checklist", {}).get("overall_risk_score", 0.5)

    log_entry = JulieLogEntry(
        log_id=f"mgr_{evidence_id[:8]}",
        agent="Manager",
        action="전략 검토 및 품질 게이트",
        input_hash=hashlib.sha256(input_str.encode()).hexdigest(),
        output_hash=hashlib.sha256(output_str.encode()).hexdigest(),
        evidence_id=evidence_id,
        trinity_score=0.92,
        confidence_score=0.92,
        impact_level="high" if risk_score > 0.7 else "medium",
        metacognition_insights={
            "quality_gate_passed": quality_gate.get("passed", False),
            "risk_score": risk_score,
            "recommendations_count": len(output_data.get("recommendations", [])),
        },
    )

    return julie_log_manager.log_agent_action(log_entry)


def log_auditor_action(
    input_data: dict[str, Any], output_data: dict[str, Any], evidence_id: str
) -> bool:
    """Auditor 레벨 액션 로깅"""
    import hashlib

    input_str = json.dumps(input_data, sort_keys=True)
    output_str = json.dumps(output_data, sort_keys=True)

    compliance_score = output_data.get("compliance_score", 0.97)
    determination = output_data.get("final_determination", {})

    log_entry = JulieLogEntry(
        log_id=f"aud_{evidence_id[:8]}",
        agent="Auditor",
        action="규정 준수 감사 및 최종 판정",
        input_hash=hashlib.sha256(input_str.encode()).hexdigest(),
        output_hash=hashlib.sha256(output_str.encode()).hexdigest(),
        evidence_id=evidence_id,
        trinity_score=0.98,
        confidence_score=0.98,
        impact_level="critical",
        source_url="https://www.irs.gov/newsroom/faqs-for-modification-of-sections-25c-25d-25e-30c-30d-45l-45w-and-179d",
        metacognition_insights={
            "compliance_score": compliance_score,
            "determination": determination.get("determination", "PENDING"),
            "two_source_verification": output_data.get("two_source_verification", {}).get(
                "verification_score", 0.0
            ),
            "evidence_bundle_created": bool(output_data.get("evidence_bundle")),
        },
    )

    return julie_log_manager.log_agent_action(log_entry)


# Trinity Score 기반 로그 분석 함수들
def analyze_agent_performance() -> dict[str, Any]:
    """AI 에이전트별 성능 분석"""
    return julie_log_manager.get_trinity_score_stats()


def get_recent_audit_trail(hours: int = 24) -> list[JulieLogEntry]:
    """최근 감사 추적 로그"""
    return julie_log_manager.get_recent_logs(hours)


def get_evidence_chain(evidence_id: str) -> list[JulieLogEntry]:
    """특정 Evidence Bundle의 전체 처리 체인"""
    return julie_log_manager.get_logs_by_evidence(evidence_id)
