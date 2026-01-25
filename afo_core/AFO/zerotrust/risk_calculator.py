"""
Trinity Risk Calculator - Zero Trust Risk Engine

This module implements the Trinity Risk calculation for Zero Trust access control.
Risk Score = (100 - Trinity Score) + Threat Factor + Context Risk

Risk > 10 → Automatic HTTP 403 Forbidden
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from AFO.services.trinity_calculator import TrinityCalculator


class ThreatLevel(Enum):
    LOW = 1
    MEDIUM = 5
    HIGH = 10
    CRITICAL = 15


class ContextRisk(Enum):
    SESSION_AGE_OLD = 4
    GEO_ANOMALY = 3
    MFA_MISSING = 2
    DEVICE_UNKNOWN = 1


@dataclass
class RiskAssessment:
    """Complete risk assessment result"""

    total_risk: float
    trinity_score: float
    threat_factor: float
    context_risk: float
    factors: list[str]
    recommendation: str
    timestamp: float

    @property
    def should_deny(self) -> bool:
        """Check if access should be denied (Risk > 10)"""
        return self.total_risk > 10.0


class TrinityRiskCalculator:
    """Zero Trust Risk Engine using Trinity Score as foundation"""

    def __init__(self) -> None:
        self.trinity_calc = TrinityCalculator()
        self.risk_threshold = 10.0  # Configurable threshold
        self.serenity_mode_threshold = 5.0  # Lower threshold for peace mode

    def calculate_risk(
        self,
        user_data: dict[str, Any],
        request_context: dict[str, Any] | None = None,
        serenity_mode: bool = False,
    ) -> RiskAssessment:
        """
        Calculate total risk score using Trinity framework

        Args:
            user_data: User authentication data
            request_context: Request metadata (IP, device, etc.)
            serenity_mode: Lower threshold for peace preservation

        Returns:
            Complete risk assessment
        """
        # 1. Get Trinity Score (foundation)
        trinity_score = self.trinity_calc.calculate_trinity_score(user_data)

        # 2. Calculate Threat Factor (external threats)
        threat_factor = self._calculate_threat_factor(request_context or {})

        # 3. Calculate Context Risk (user behavior)
        context_risk = self._calculate_context_risk(user_data, request_context or {})

        # 4. Total Risk = (100 - TS) + TF + CR
        total_risk = (100.0 - trinity_score) + threat_factor + context_risk

        # 5. Build factors list
        factors = []
        if threat_factor > 0:
            factors.append(f"Threat Factor: {threat_factor}")
        if context_risk > 0:
            factors.append(f"Context Risk: {context_risk}")

        # 6. Determine recommendation
        threshold = self.serenity_mode_threshold if serenity_mode else self.risk_threshold
        if total_risk > threshold:
            recommendation = f"ACCESS_DENIED: Risk {total_risk:.1f} > threshold {threshold}"
        else:
            recommendation = f"ACCESS_GRANTED: Risk {total_risk:.1f} ≤ threshold {threshold}"

        return RiskAssessment(
            total_risk=total_risk,
            trinity_score=trinity_score,
            threat_factor=threat_factor,
            context_risk=context_risk,
            factors=factors,
            recommendation=recommendation,
            timestamp=time.time(),
        )

    def _calculate_threat_factor(self, request_context: dict[str, Any]) -> float:
        """Calculate external threat factor"""
        threat_score = 0.0

        # IP reputation check (simplified)
        client_ip = request_context.get("client_ip", "")
        if self._is_suspicious_ip(client_ip):
            threat_score += ThreatLevel.HIGH.value

        # Rate limiting check
        request_count = request_context.get("request_count_last_minute", 0)
        if request_count > 100:
            threat_score += ThreatLevel.CRITICAL.value
        elif request_count > 50:
            threat_score += ThreatLevel.HIGH.value

        # User agent anomaly
        user_agent = request_context.get("user_agent", "")
        if self._is_suspicious_user_agent(user_agent):
            threat_score += ThreatLevel.MEDIUM.value

        return min(threat_score, 20.0)  # Cap at 20

    def _calculate_context_risk(
        self, user_data: dict[str, Any], request_context: dict[str, Any]
    ) -> float:
        """Calculate user context risk"""
        risk_score = 0.0

        # Session age check
        session_created = user_data.get("session_created", 0)
        if time.time() - session_created > 3600:  # 1 hour
            risk_score += ContextRisk.SESSION_AGE_OLD.value

        # Geographic anomaly (simplified)
        current_geo = request_context.get("geo_location", "")
        usual_geo = user_data.get("usual_location", "")
        if current_geo and usual_geo and current_geo != usual_geo:
            risk_score += ContextRisk.GEO_ANOMALY.value

        # MFA status
        has_mfa = user_data.get("mfa_enabled", False)
        if not has_mfa:
            risk_score += ContextRisk.MFA_MISSING.value

        # Device posture
        device_fingerprint = request_context.get("device_fingerprint", "")
        known_devices = user_data.get("known_devices", [])
        if device_fingerprint and device_fingerprint not in known_devices:
            risk_score += ContextRisk.DEVICE_UNKNOWN.value

        return risk_score

    def _is_suspicious_ip(self, ip: str) -> bool:
        """Check if IP is suspicious (simplified)"""
        # This would integrate with threat intelligence feeds
        suspicious_prefixes = ["10.", "192.168.", "172."]
        return any(ip.startswith(prefix) for prefix in suspicious_prefixes)

    def _is_suspicious_user_agent(self, ua: str) -> bool:
        """Check if user agent is suspicious (simplified)"""
        suspicious_patterns = ["curl", "wget", "python-requests"]
        return any(pattern in ua.lower() for pattern in suspicious_patterns)


# FastAPI Dependency for Zero Trust protection
def risk_guard(
    risk_calc: TrinityRiskCalculator | None = None, serenity_mode: bool = False
) -> callable:
    """
    FastAPI dependency for Zero Trust risk-based access control

    Usage:
        @app.get("/protected")
        async def protected_endpoint(
            user = Depends(auth_user),
            _ = Depends(risk_guard())
        ):
            return {"message": "Access granted"}
    """
    if risk_calc is None:
        risk_calc = TrinityRiskCalculator()

    async def guard(
        user_data: dict[str, Any], request_context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        assessment = risk_calc.calculate_risk(
            user_data=user_data,
            request_context=request_context,
            serenity_mode=serenity_mode,
        )

        if assessment.should_deny:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=403, detail=f"Access denied: {assessment.recommendation}"
            )

        return user_data

    return guard
