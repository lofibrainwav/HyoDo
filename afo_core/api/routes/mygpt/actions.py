"""
MyGPT Actions Integration - Phase 84
TICKET-116: MyGPT Action 스키마 연동 및 테스트

Gateway API들을 MyGPT Actions으로 변환하여 외부 플랫폼 연동
OpenAI ChatGPT Custom Actions 스펙 준수
"""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# Create router
actions_router = APIRouter(
    prefix="/mygpt/actions",
    tags=["mygpt-actions"],
    responses={
        404: {"description": "Action not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)


# MyGPT Actions 스키마 모델들
class MyGPTActionSchema(BaseModel):
    """MyGPT Action 스키마"""

    openapi: str = Field(default="3.0.1", description="OpenAPI 버전")
    info: dict[str, Any] = Field(..., description="API 정보")
    servers: list[dict[str, Any]] = Field(..., description="서버 목록")
    paths: dict[str, Any] = Field(..., description="API 경로들")
    components: dict[str, Any] = Field(..., description="컴포넌트 정의")


class MyGPTActionConfig(BaseModel):
    """MyGPT Action 설정"""

    action_id: str = Field(..., description="액션 ID")
    name: str = Field(..., description="액션 이름")
    description: str = Field(..., description="액션 설명")
    schema_url: str = Field(..., description="스키마 URL")
    auth_type: str = Field(default="bearer", description="인증 타입")
    enabled: bool = Field(default=True, description="활성화 여부")


# MyGPT Actions 구현
@actions_router.get("/schema", response_model=MyGPTActionSchema)
async def get_mygpt_actions_schema() -> MyGPTActionSchema:
    """
    Julie CPA Gateway API들의 MyGPT Actions OpenAPI 스키마

    MyGPT(ChatGPT)가 Gateway API들을 호출할 수 있도록 하는 스키마를 제공합니다.
    """
    try:
        logger.info("Generating MyGPT Actions schema for Gateway APIs")

        # Gateway API들의 OpenAPI 스키마 생성
        schema = MyGPTActionSchema(
            info={
                "title": "Julie CPA Gateway API",
                "description": "AFO Kingdom의 Julie CPA 세무 분석 및 감사 API",
                "version": "1.0.0",
                "contact": {
                    "name": "AFO Kingdom Support",
                    "url": "https://jangjungwha.com",
                    "email": "support@jangjungwha.com",
                },
            },
            servers=[
                {"url": "https://api.jangjungwha.com", "description": "Production server"},
                {"url": "http://localhost:8010", "description": "Development server"},
            ],
            paths={
                "/api/gateway/analyze": {
                    "post": {
                        "summary": "세무 문서 AI 분석",
                        "description": "AI 기반 세무 문서 분석 및 전문가 조언 제공",
                        "operationId": "analyzeTaxDocument",
                        "tags": ["tax-analysis"],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TaxAnalysisRequest"}
                                }
                            },
                        },
                        "responses": {
                            "200": {
                                "description": "분석 성공",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/TaxAnalysisResponse"
                                        }
                                    }
                                },
                            },
                            "422": {"description": "입력 검증 오류"},
                            "500": {"description": "서버 오류"},
                        },
                        "security": [{"bearerAuth": []}],
                    }
                },
                "/api/gateway/review": {
                    "post": {
                        "summary": "세무 보고서 리뷰",
                        "description": "세무 보고서 전문가 리뷰 및 최적화 제안",
                        "operationId": "reviewTaxReturn",
                        "tags": ["tax-review"],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TaxReviewRequest"}
                                }
                            },
                        },
                        "responses": {
                            "200": {
                                "description": "리뷰 성공",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/TaxReviewResponse"}
                                    }
                                },
                            }
                        },
                        "security": [{"bearerAuth": []}],
                    }
                },
                "/api/gateway/audit": {
                    "post": {
                        "summary": "세무 감사 지원",
                        "description": "세무 감사 준비 및 지원 서비스",
                        "operationId": "auditTaxPreparation",
                        "tags": ["tax-audit"],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TaxAuditRequest"}
                                }
                            },
                        },
                        "responses": {
                            "200": {
                                "description": "감사 지원 성공",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/TaxAuditResponse"}
                                    }
                                },
                            }
                        },
                        "security": [{"bearerAuth": []}],
                    }
                },
                "/api/gateway/irs/updates": {
                    "get": {
                        "summary": "IRS 규정 변경 알림",
                        "description": "최신 IRS 규정 변경사항 조회",
                        "operationId": "getIRSUpdates",
                        "tags": ["irs-monitoring"],
                        "parameters": [
                            {
                                "name": "days",
                                "in": "query",
                                "description": "조회 기간 (일)",
                                "required": False,
                                "schema": {
                                    "type": "integer",
                                    "default": 30,
                                    "minimum": 1,
                                    "maximum": 365,
                                },
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "조회 성공",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/IRSUpdateResponse"}
                                    }
                                },
                            }
                        },
                    }
                },
                "/api/gateway/irs/impact": {
                    "post": {
                        "summary": "규정 변경 영향 분석",
                        "description": "IRS 규정 변경의 세무적 영향 분석",
                        "operationId": "analyzeIRSImpact",
                        "tags": ["irs-analysis"],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/IRSImpactRequest"}
                                }
                            },
                        },
                        "responses": {
                            "200": {
                                "description": "분석 성공",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/IRSImpactResponse"}
                                    }
                                },
                            }
                        },
                        "security": [{"bearerAuth": []}],
                    }
                },
                "/api/gateway/kingdom/status": {
                    "get": {
                        "summary": "왕국 시스템 상태",
                        "description": "Julie CPA 왕국의 시스템 상태 조회",
                        "operationId": "getKingdomStatus",
                        "tags": ["system-status"],
                        "responses": {
                            "200": {
                                "description": "상태 조회 성공",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/KingdomStatusResponse"
                                        }
                                    }
                                },
                            }
                        },
                    }
                },
            },
            components={
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
                },
                "schemas": {
                    # Request Schemas
                    "TaxAnalysisRequest": {
                        "type": "object",
                        "required": ["document_text"],
                        "properties": {
                            "document_text": {
                                "type": "string",
                                "minLength": 10,
                                "maxLength": 100000,
                                "description": "분석할 세무 문서 텍스트",
                            },
                            "document_type": {
                                "type": "string",
                                "default": "general",
                                "enum": [
                                    "tax_return",
                                    "financial_statement",
                                    "irs_notice",
                                    "business_expense",
                                ],
                                "description": "문서 유형",
                            },
                            "analysis_focus": {
                                "type": "array",
                                "items": {"type": "string"},
                                "default": ["compliance", "optimization"],
                                "description": "분석 초점",
                            },
                            "priority": {
                                "type": "string",
                                "default": "normal",
                                "enum": ["low", "normal", "high", "urgent"],
                                "description": "처리 우선순위",
                            },
                        },
                    },
                    "TaxReviewRequest": {
                        "type": "object",
                        "required": ["tax_return_data"],
                        "properties": {
                            "tax_return_data": {
                                "type": "object",
                                "description": "세무 보고서 데이터",
                            },
                            "review_type": {
                                "type": "string",
                                "default": "comprehensive",
                                "enum": ["comprehensive", "quick_check", "audit_prep"],
                                "description": "리뷰 유형",
                            },
                            "include_benchmarks": {
                                "type": "boolean",
                                "default": True,
                                "description": "벤치마크 비교 포함 여부",
                            },
                        },
                    },
                    "TaxAuditRequest": {
                        "type": "object",
                        "required": ["audit_scope", "time_period"],
                        "properties": {
                            "audit_scope": {
                                "type": "string",
                                "enum": ["income_tax", "sales_tax", "payroll_tax", "all"],
                                "description": "감사 범위",
                            },
                            "time_period": {"type": "string", "description": "감사 기간"},
                            "focus_areas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "default": ["documentation", "calculations", "compliance"],
                                "description": "집중 영역",
                            },
                            "include_mock_audit": {
                                "type": "boolean",
                                "default": True,
                                "description": "모의 감사 포함 여부",
                            },
                        },
                    },
                    "IRSImpactRequest": {
                        "type": "object",
                        "required": ["regulation_change", "client_profile"],
                        "properties": {
                            "regulation_change": {
                                "type": "string",
                                "description": "변경된 규정 설명",
                            },
                            "client_profile": {
                                "type": "object",
                                "description": "클라이언트 프로필",
                            },
                            "analysis_depth": {
                                "type": "string",
                                "default": "standard",
                                "enum": ["basic", "standard", "comprehensive"],
                                "description": "분석 깊이",
                            },
                        },
                    },
                    # Response Schemas
                    "TaxAnalysisResponse": {
                        "type": "object",
                        "properties": {
                            "analysis_id": {"type": "string"},
                            "document_type": {"type": "string"},
                            "compliance_score": {"type": "number", "minimum": 0, "maximum": 100},
                            "risk_level": {"type": "string"},
                            "optimization_opportunities": {
                                "type": "array",
                                "items": {"type": "object"},
                            },
                            "key_findings": {"type": "array", "items": {"type": "string"}},
                            "recommendations": {"type": "array", "items": {"type": "string"}},
                            "evidence_bundle_id": {"type": "string"},
                            "trinity_score": {"type": "object"},
                            "processing_time": {"type": "number"},
                            "analyzed_at": {"type": "string", "format": "date-time"},
                        },
                    },
                    "TaxReviewResponse": {
                        "type": "object",
                        "properties": {
                            "review_id": {"type": "string"},
                            "overall_assessment": {"type": "string"},
                            "compliance_status": {"type": "string"},
                            "risk_areas": {"type": "array", "items": {"type": "object"}},
                            "optimization_suggestions": {
                                "type": "array",
                                "items": {"type": "object"},
                            },
                            "benchmark_comparison": {"type": "object"},
                            "evidence_bundle_id": {"type": "string"},
                            "reviewed_at": {"type": "string", "format": "date-time"},
                        },
                    },
                    "TaxAuditResponse": {
                        "type": "object",
                        "properties": {
                            "audit_id": {"type": "string"},
                            "audit_readiness_score": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 100,
                            },
                            "critical_findings": {"type": "array", "items": {"type": "object"}},
                            "documentation_status": {"type": "object"},
                            "recommended_actions": {"type": "array", "items": {"type": "string"}},
                            "mock_audit_results": {"type": "object"},
                            "evidence_bundle_id": {"type": "string"},
                            "audited_at": {"type": "string", "format": "date-time"},
                        },
                    },
                    "IRSUpdateResponse": {
                        "type": "object",
                        "properties": {
                            "updates": {"type": "array", "items": {"type": "object"}},
                            "last_updated": {"type": "string", "format": "date-time"},
                            "total_changes": {"type": "integer"},
                        },
                    },
                    "IRSImpactResponse": {
                        "type": "object",
                        "properties": {
                            "impact_id": {"type": "string"},
                            "overall_impact": {"type": "string"},
                            "financial_impact": {"type": "object"},
                            "compliance_changes": {"type": "array", "items": {"type": "string"}},
                            "action_items": {"type": "array", "items": {"type": "object"}},
                            "deadline_info": {"type": "object"},
                            "evidence_bundle_id": {"type": "string"},
                            "analyzed_at": {"type": "string", "format": "date-time"},
                        },
                    },
                    "KingdomStatusResponse": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "version": {"type": "string"},
                            "uptime": {"type": "string"},
                            "services": {"type": "object"},
                            "trinity_score": {"type": "object"},
                            "last_updated": {"type": "string", "format": "date-time"},
                        },
                    },
                },
            },
        )

        logger.info("MyGPT Actions schema generated successfully")
        return schema

    except Exception as e:
        logger.error(f"Failed to generate MyGPT Actions schema: {e}")
        raise HTTPException(
            status_code=500, detail="MyGPT Actions 스키마 생성 중 오류가 발생했습니다."
        )


@actions_router.get("/config", response_model=MyGPTActionConfig)
async def get_mygpt_actions_config() -> MyGPTActionConfig:
    """
    MyGPT Actions 설정 정보

    MyGPT에서 사용할 액션 설정을 반환합니다.
    """
    try:
        config = MyGPTActionConfig(
            action_id="julie-cpa-gateway",
            name="Julie CPA Gateway",
            description="AFO Kingdom의 Julie CPA 세무 분석 및 감사 API를 MyGPT에서 사용할 수 있는 액션",
            schema_url="https://api.jangjungwha.com/mygpt/actions/schema",
            auth_type="bearer",
            enabled=True,
        )

        return config

    except Exception as e:
        logger.error(f"Failed to get MyGPT Actions config: {e}")
        raise HTTPException(
            status_code=500, detail="MyGPT Actions 설정 조회 중 오류가 발생했습니다."
        )


@actions_router.get("/openapi.json")
async def get_openapi_json():
    """
    OpenAPI JSON 스키마 다운로드

    MyGPT Custom Actions 설정에 사용할 수 있는 OpenAPI 스펙을 JSON으로 제공합니다.
    """
    try:
        schema = await get_mygpt_actions_schema()
        return JSONResponse(content=schema.model_dump())

    except Exception as e:
        logger.error(f"Failed to generate OpenAPI JSON: {e}")
        raise HTTPException(status_code=500, detail="OpenAPI JSON 생성 중 오류가 발생했습니다.")


@actions_router.get("/test")
async def test_mygpt_actions():
    """
    MyGPT Actions 테스트 엔드포인트

    MyGPT Actions 설정이 올바른지 테스트합니다.
    """
    try:
        # 스키마 생성 테스트
        schema = await get_mygpt_actions_schema()

        # 설정 조회 테스트
        config = await get_mygpt_actions_config()

        return {
            "status": "success",
            "message": "MyGPT Actions 설정이 정상 작동합니다",
            "schema_endpoints": len(schema.paths),
            "action_id": config.action_id,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"MyGPT Actions test failed: {e}")
        return {
            "status": "error",
            "message": f"MyGPT Actions 테스트 실패: {e!s}",
            "timestamp": datetime.now(UTC).isoformat(),
        }


# Export router for main API server
__all__ = ["actions_router"]
