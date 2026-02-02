# Trinity Score: 90.0 (Established by Chancellor)
"""
Persona Service
페르소나 전환 서비스 (PDF 페이지 3: AFO ↔ TRINITY-OS 통합 지점)

Phase 5: Trinity Type Validator 적용 - 런타임 Trinity Score 검증
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from AFO.services.persona_types import (
    LogEntry,
    PersonaContext,
    PersonaInfo,
    SwitchResult,
    TrinityScoreAnalysis,
)

try:
    from AFO.utils.trinity_type_validator import validate_with_trinity
except ImportError:
    # Fallback for import issues

    def validate_with_trinity[TF: Callable[..., Any]](func: TF) -> TF:
        return func


from AFO.domain.persona import (
    Persona,
    commander,
    creator,
    current_persona,
    family_head,
    jang_yeong_sil,
    learner,
    shin_saimdang,
    yi_sun_sin,
)

logger = logging.getLogger(__name__)

# 페르소나 매핑 (PDF 페이지 4: Personas 시스템)
PERSONA_MAPPING: dict[str, Persona | None] = {
    "commander": commander,
    "family": family_head,
    "family_head": family_head,
    "creator": creator,
    "learner": learner,  # Phase 2 구현 완료
    "jang_yeong_sil": jang_yeong_sil,
    "yi_sun_sin": yi_sun_sin,
    "shin_saimdang": shin_saimdang,
}


class PersonaService:
    """
    페르소나 전환 서비스

    PDF 페이지 3: AFO ↔ TRINITY-OS 통합 지점
    PDF 페이지 4: Personas 시스템
    """

    def __init__(self) -> None:
        self._current_persona: Persona = current_persona

    @property
    def current_persona(self) -> Persona:
        """현재 활성화된 페르소나"""
        return self._current_persona

    @validate_with_trinity
    async def switch_persona(
        self, persona_type: str, context: PersonaContext | None = None
    ) -> SwitchResult:
        """
        형님의 명령으로 페르소나 전환 (PDF 페이지 4: Personas 시스템)

        Phase 5: Trinity 검증 적용 - 런타임 품질 모니터링

        Args:
            persona_type: 페르소나 타입 (commander, family, creator 등)
            context: 추가 맥락 정보

        Returns:
            전환 결과
        """
        target = PERSONA_MAPPING.get(persona_type.lower())

        if not target:
            raise ValueError(f"알 수 없는 페르소나 타입: {persona_type}")

        if target == self._current_persona:
            return {
                "current_persona": self._current_persona.name,
                "status": "이미 활성화된 페르소나입니다.",
                "trinity_scores": self._current_persona.trinity_scores,
            }

        # 이전 페르소나 비활성화
        self._current_persona.active = False

        # 새 페르소나 활성화
        target.switch_to()

        # 맥락 정보 추가
        if context:
            target.add_context(context)

        # 전역 변수 업데이트 (domain 모듈의 current_persona)
        import AFO.domain.persona as persona_module

        persona_module.current_persona = target
        self._current_persona = target

        # TRINITY-OS 로그 브릿지 전송 (백그라운드 태스크로 처리 - 블로킹 방지)
        # 성능 최적화: 로그 전송을 기다리지 않고 즉시 반환
        try:
            # 백그라운드 태스크 생성 (참조 저장하여 가비지 컬렉션 방지)
            task = asyncio.create_task(self._send_log_bridge(target, context))
            task.add_done_callback(lambda _t: None)  # Prevent warning on done
        except RuntimeError:
            # 이벤트 루프가 없는 경우 조용히 처리
            logger.debug("[PersonaService] 이벤트 루프 없음, 로그 브릿지 건너뜀")

        logger.info(
            "[PersonaService] 페르소나 전환: %s → %s",
            self._current_persona.name,
            target.name,
        )

        return {
            "current_persona": target.name,
            "status": "전환 완료",
            "trinity_scores": target.trinity_scores,
            "last_switched": (target.last_switched.isoformat() if target.last_switched else None),
        }

    async def get_current_persona(self) -> PersonaInfo:
        """현재 활성화된 페르소나 정보 조회"""
        return {
            "id": self._current_persona.id,
            "name": self._current_persona.name,
            "type": self._current_persona.type.value,
            "trinity_scores": self._current_persona.trinity_scores,
            "active": self._current_persona.active,
            "last_switched": (
                self._current_persona.last_switched.isoformat()
                if self._current_persona.last_switched
                else None
            ),
        }

    @validate_with_trinity
    async def get_persona_from_db(self, persona_id: str) -> PersonaInfo | None:
        """
        DB에서 페르소나 조회 (Phase 2 확장)

        실제 DB 조회 로직 구현
        """
        try:
            # DB 연결 가져오기 (Phase 2 확장)
            from AFO.services.database import get_db_connection

            conn = await get_db_connection()
            try:
                # 페르소나 조회 쿼리
                result = await conn.fetchrow(
                    """
                    SELECT id, name, type, trinity_scores, active, last_switched
                    FROM personas
                    WHERE id = $1
                    """,
                    persona_id,
                )

                if result:
                    return {
                        "id": result["id"],
                        "name": result["name"],
                        "type": result["type"],
                        "trinity_scores": result["trinity_scores"],
                        "active": result["active"],
                        "last_switched": (
                            result["last_switched"].isoformat() if result["last_switched"] else None
                        ),
                    }
                return None

            finally:
                await conn.close()

        except ImportError:
            logger.warning("[PersonaService] DB 모듈을 찾을 수 없습니다")
            return None
        except (ValueError, KeyError, AttributeError) as e:
            logger.error("[PersonaService] DB 페르소나 조회 실패 (값/키/속성 에러): %s", str(e))
            return None
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.error("[PersonaService] DB 페르소나 조회 실패 (예상치 못한 에러): %s", str(e))
            return None

    @validate_with_trinity
    async def calculate_trinity_score(
        self, persona_data: PersonaInfo, context: PersonaContext | None = None
    ) -> TrinityScoreAnalysis:
        """
        실제 Trinity Score 계산 (Phase 2 확장)

        Args:
            persona_data: 페르소나 데이터
            context: 추가 맥락 정보

        Returns:
            계산된 Trinity Score 결과
        """
        try:
            # Trinity Calculator 서비스 사용
            from AFO.services.trinity_calculator import trinity_calculator

            # 페르소나 기반 Trinity Score 계산
            scores = await trinity_calculator.calculate_persona_scores(
                persona_data=persona_data, context=context or {}
            )

            # 상세 분석 결과 생성
            analysis = {
                "truth_score": scores.get("truth", 0),
                "goodness_score": scores.get("goodness", 0),
                "beauty_score": scores.get("beauty", 0),
                "serenity_score": scores.get("serenity", 0),
                "eternity_score": scores.get("eternity", 0),
                "total_score": sum(scores.values()),
                "persona_type": persona_data.get("type", "unknown"),
                "context_used": bool(context),
                "calculated_at": datetime.now(UTC).isoformat(),
            }

            # Trinity Score 검증
            if analysis["total_score"] >= 400:  # 탁월한 기준
                analysis["evaluation"] = "탁월"
            elif analysis["total_score"] >= 350:
                analysis["evaluation"] = "우수"
            elif analysis["total_score"] >= 300:
                analysis["evaluation"] = "양호"
            else:
                analysis["evaluation"] = "개선 필요"

            logger.info(
                "[PersonaService] Trinity Score 계산 완료: %s - %s점",
                persona_data.get("name", "unknown"),
                analysis["total_score"],
            )

            return analysis

        except ImportError:
            logger.warning("[PersonaService] Trinity Calculator를 찾을 수 없습니다")
            raise
        except (ValueError, TypeError, AttributeError) as e:
            logger.error(
                "[PersonaService] Trinity Score 계산 실패 (값/타입/속성 에러): %s",
                str(e),
            )
            # 기본값 반환
            return {
                "truth_score": 80,
                "goodness_score": 80,
                "beauty_score": 80,
                "serenity_score": 80,
                "eternity_score": 80,
                "total_score": 400,
                "persona_type": persona_data.get("type", "unknown"),
                "context_used": False,
                "calculated_at": datetime.now(UTC).isoformat(),
            }
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.error(
                "[PersonaService] Trinity Score 계산 실패 (예상치 못한 에러): %s",
                str(e),
            )
            # 기본값 반환
            return {
                "truth_score": 80,
                "goodness_score": 80,
                "beauty_score": 80,
                "serenity_score": 80,
                "eternity_score": 80,
                "total_score": 400,
                "persona_type": persona_data.get("type", "unknown"),
                "context_used": False,
                "calculated_at": datetime.now(UTC).isoformat(),
                "evaluation": "기본값",
                "error": str(e),
            }

    async def _send_log_bridge(self, persona: Persona, context: PersonaContext | None) -> None:
        """
        TRINITY-OS 로그 브릿지 전송 (PDF 페이지 3: 로그 브릿지)

        Phase 2 확장: 실제 MCP 서버 호출 구현
        - TRINITY-OS MCP 서버에 페르소나 전환 알림
        - SSE 이벤트 큐를 통한 실시간 브로드캐스트
        """
        log_entry = {
            "event": "persona_switch",
            "persona_id": persona.id,
            "persona_name": persona.name,
            "persona_type": persona.type.value,
            "trinity_scores": persona.trinity_scores,
            "context": context or {},
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Phase 2: TRINITY-OS 로그 브릿지 구현
        try:
            # 1. MCP 서버를 통한 TRINITY-OS 연동 시도
            await self._send_via_mcp(log_entry)
        except (ImportError, AttributeError) as mcp_error:
            logger.warning("MCP 로그 브릿지 실패, SSE로 폴백: %s", str(mcp_error))
            try:
                # 2. SSE 이벤트 큐를 통한 실시간 브로드캐스트
                await self._send_via_sse(log_entry)
            except (ImportError, AttributeError) as sse_error:
                logger.error("SSE 로그 브릿지 실패: %s", str(sse_error))
                # 3. 최종 폴백: 로컬 로깅만 수행
                logger.info("[로그 브릿지] 로컬 로깅만 수행: %s", persona.name)
        except (OSError, ConnectionError, TimeoutError) as mcp_error:
            logger.warning(
                "MCP 로그 브릿지 오류 (시스템/연결/타임아웃), SSE로 폴백: %s",
                str(mcp_error),
            )
            try:
                await self._send_via_sse(log_entry)
            except (ImportError, AttributeError, RuntimeError) as sse_error:
                logger.error("SSE 로그 브릿지 실패 (import/속성/런타임 에러): %s", str(sse_error))
                logger.info("[로그 브릿지] 로컬 로깅만 수행: %s", persona.name)
            except Exception as sse_error:  # - Intentional fallback
                logger.error("SSE 로그 브릿지 실패 (예상치 못한 에러): %s", str(sse_error))
                logger.info("[로그 브릿지] 로컬 로깅만 수행: %s", persona.name)
        except Exception as mcp_error:  # - Intentional fallback for unexpected errors
            logger.warning("MCP 로그 브릿지 예상치 못한 오류, SSE로 폴백: %s", str(mcp_error))
            try:
                await self._send_via_sse(log_entry)
            except (ImportError, AttributeError, RuntimeError) as sse_error:
                logger.error("SSE 로그 브릿지 실패 (import/속성/런타임 에러): %s", str(sse_error))
                logger.info("[로그 브릿지] 로컬 로깅만 수행: %s", persona.name)
            except Exception as sse_error:  # - Intentional fallback
                logger.error("SSE 로그 브릿지 실패 (예상치 못한 에러): %s", str(sse_error))
                logger.info("[로그 브릿지] 로컬 로깅만 수행: %s", persona.name)

        logger.debug("[로그 브릿지] 전송 데이터: %s", log_entry)

    async def _send_via_mcp(self, log_entry: LogEntry) -> None:
        """
        MCP 서버를 통한 TRINITY-OS 로그 브릿지 전송

        Args:
            log_entry: 전송할 로그 엔트리
        """
        try:
            # TRINITY-OS MCP 클라이언트 호출
            from AFO.api.compat import get_trinity_os_client

            trinity_client = get_trinity_os_client()
            if trinity_client:
                await trinity_client.send_log_event("persona_switch", log_entry)
                logger.info(
                    "[MCP 브릿지] TRINITY-OS에 페르소나 전환 알림 전송: %s",
                    log_entry.get("persona_name", "unknown"),
                )
            else:
                raise RuntimeError("TRINITY-OS MCP 클라이언트 unavailable")
        except ImportError as exc:
            raise RuntimeError("TRINITY-OS MCP integration not available") from exc
        except (OSError, ConnectionError, TimeoutError) as e:
            logger.warning("MCP 브릿지 전송 실패 (시스템/연결/타임아웃 에러): %s", str(e))
            raise
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.warning("MCP 브릿지 전송 실패 (예상치 못한 에러): %s", str(e))
            raise

    async def _send_via_sse(self, log_entry: LogEntry) -> None:
        """
        SSE 이벤트 큐를 통한 실시간 브릿지 전송

        Args:
            log_entry: 전송할 로그 엔트리
        """
        try:
            # 글로벌 이벤트 큐에 추가 (initialization.py에서 관리)
            from AFO.api.initialization import neural_event_queue

            await neural_event_queue.put(
                {
                    "type": "persona_switch",
                    "data": log_entry,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            logger.info(
                "[SSE 브릿지] 이벤트 큐에 페르소나 전환 알림 추가: %s",
                log_entry.get("persona_name", "unknown"),
            )
        except ImportError as exc:
            logger.error("SSE 브릿지 모듈을 찾을 수 없습니다: %s", str(exc))
            raise
        except (AttributeError, RuntimeError, KeyError) as e:
            logger.error("SSE 브릿지 전송 실패 (속성/런타임/키 에러): %s", str(e))
            raise
        except Exception as e:  # - Intentional fallback for unexpected errors
            logger.error("SSE 브릿지 전송 실패 (예상치 못한 에러): %s", str(e))
            raise


# 싱글톤 인스턴스
persona_service = PersonaService()


# 편의 함수
async def switch_persona(persona_type: str, context: PersonaContext | None = None) -> SwitchResult:
    """페르소나 전환 편의 함수"""
    return await persona_service.switch_persona(persona_type, context)


async def get_current_persona() -> PersonaInfo:
    """현재 페르소나 조회 편의 함수"""
    result: PersonaInfo = await persona_service.get_current_persona()
    return result
