"""
Security Gate - 보안 검증 및 제어

善 (Yi Sun-sin): 보안/리스크 평가
- PII 데이터 식별
- 보안 게이트 정의
- 권한 검증
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """보안 레벨"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PIIType:
    """PII 데이터 타입"""

    name: str
    pattern: str
    severity: SecurityLevel
    description: str


class PIIClassifier:
    """PII 데이터 식별자"""

    SSN_PATTERNS = [
        r"\b\d{3}-\d{2}-\d{4}\b",  # XXX-XX-XXXX
        r"\b\d{2}-\d{7}\b",  # XX-XXXXXXX
        r"\b\d{9}\b",  # XXXXXXXXXX
    ]

    CREDIT_CARD_PATTERNS = [
        r"\b(?:\d{16}|\d{4}[- ]\d{4}[- ]\d{4}[- ]\d{4})\b",  # 16 digits or groups of 4
        r"\b(?:3[47]\d{13}|5[1-5]\d{14}|6(?:011|5[0-2][0-9])\d{12})\b",  # Card prefixes
    ]

    PERSONAL_INFO_PATTERNS = [
        r"\b(?:birth[_\s]date|dob)[:\s]+(?:\d{1,2}[-/\s]\d{1,2}[-/\s]\d{2,4})\b",
        r"\b(?:driver['\s]?license|dl)[#]?\s*[\w\s-]+",
    ]

    CONTACT_INFO_PATTERNS = [
        r"\b(?:email|e[-\s]?mail)[:]\s*[\w.-]+@[\w.-]+\.\w+\b",
        r"\b(?:phone|tel)[#]?\s*(?:\+?(\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        r"\b(?:address|addr)[#]?\s*(?:\d+\s+[\w\s]+\s+street|\w+\s+street)",
    ]

    @staticmethod
    def classify_pii(text: str) -> list[dict[str, Any]]:
        """
        PII 데이터 식별

        Args:
            text: 분석할 텍스트

        Returns:
            PII 식별 결과 리스트
            [
                {
                    "type": str,  # PII 타입
                    "pattern": str,  # 매칭된 패턴
                    "match": str,  # 매칭된 텍스트
                    "severity": SecurityLevel,  # 보안 레벨
                    "start": int,  # 시작 위치
                    "end": int,  # 종료 위치
                },
                ...
            ]
        """
        results = []

        # SSN 패턴 검색
        for i, pattern in enumerate(PIIClassifier.SSN_PATTERNS, 1):
            for match in re.finditer(pattern, text, re.IGNORECASE):
                results.append(
                    {
                        "type": "SSN",
                        "pattern": pattern,
                        "match": match.group(),
                        "severity": SecurityLevel.CRITICAL,
                        "start": match.start(),
                        "end": match.end(),
                    }
                )
                logger.warning(f"PII 식별: SSN ({match.group()}) [{match.start()}:{match.end()}]")

        # 신용카드 패턴 검색
        for i, pattern in enumerate(PIIClassifier.CREDIT_CARD_PATTERNS, 1):
            for match in re.finditer(pattern, text):
                results.append(
                    {
                        "type": "Credit Card",
                        "pattern": pattern,
                        "match": match.group()[:10] + "..."
                        if len(match.group()) > 10
                        else match.group(),
                        "severity": SecurityLevel.CRITICAL,
                        "start": match.start(),
                        "end": match.end(),
                    }
                )
                logger.warning(
                    f"PII 식별: Credit Card ({match.group()[:10]}...) "
                    f"[{match.start()}:{match.end()}]"
                )

        # 개인정보 패턴 검색
        for i, pattern in enumerate(PIIClassifier.PERSONAL_INFO_PATTERNS, 1):
            for match in re.finditer(pattern, text, re.IGNORECASE):
                results.append(
                    {
                        "type": "Personal Info",
                        "pattern": pattern,
                        "match": match.group(),
                        "severity": SecurityLevel.HIGH,
                        "start": match.start(),
                        "end": match.end(),
                    }
                )
                logger.warning(
                    f"PII 식별: Personal Info ({match.group()}) [{match.start()}:{match.end()}]"
                )

        # 연락처 패턴 검색
        for i, pattern in enumerate(PIIClassifier.CONTACT_INFO_PATTERNS, 1):
            for match in re.finditer(pattern, text, re.IGNORECASE):
                results.append(
                    {
                        "type": "Contact Info",
                        "pattern": pattern,
                        "match": match.group()[:20] + "..."
                        if len(match.group()) > 20
                        else match.group(),
                        "severity": SecurityLevel.HIGH,
                        "start": match.start(),
                        "end": match.end(),
                    }
                )
                logger.warning(
                    f"PII 식별: Contact Info ({match.group()[:20]}...) "
                    f"[{match.start()}:{match.end()}]"
                )

        logger.info(f"PII 분석 완료: {len(results)}개 항목 식별")

        return results

    @staticmethod
    def mask_pii(text: str, pii_results: list[dict[str, Any]]) -> str:
        """
        PII 마스킹

        Args:
            text: 원본 텍스트
            pii_results: PII 식별 결과

        Returns:
            마스킹된 텍스트
        """
        masked_text = text

        # 결과를 종료 위치 기준 내림차순 정렬
        sorted_results = sorted(pii_results, key=lambda x: x["end"], reverse=True)

        for result in sorted_results:
            match_text = result["match"]
            start = result["start"]
            end = result["end"]

            severity = result["severity"]

            # 심각도별 마스킹
            if severity == SecurityLevel.CRITICAL:
                masked = "*" * len(match_text)
            elif severity == SecurityLevel.HIGH:
                masked = match_text[:3] + "*" * (len(match_text) - 3)
            else:
                masked = match_text[:4] + "*" * (len(match_text) - 4)

            masked_text = masked_text[:start] + masked + masked_text[end:]

        logger.info(f"PII 마스킹 완료: {len(sorted_results)}개 항목 마스킹")

        return masked_text

    @staticmethod
    def has_pii(text: str) -> bool:
        """
        PII 포함 여부 확인

        Args:
            text: 분석할 텍스트

        Returns:
            True if PII 포함, False if 아님
        """
        results = PIIClassifier.classify_pii(text)
        has_pii = len(results) > 0

        if has_pii:
            logger.warning(f"PII 포함 감지: {len(results)}개 항목")
        else:
            logger.debug("PII 포함하지 않음")

        return has_pii


class SecurityGate:
    """보안 게이트"""

    @staticmethod
    def check_data_security(
        data: str | dict[str, Any],
        pii_check: bool = True,
        size_limit_mb: int = 10,
    ) -> dict[str, Any]:
        """
        데이터 보안 검증

        Args:
            data: 검증할 데이터
            pii_check: PII 검사 수행 여부
            size_limit_mb: 크기 제한 (MB)

        Returns:
            보안 검증 결과
            {
                "passed": bool,  # 검증 통과 여부
                "violations": list,  # 위반 사항
                "risk_score": float,  # 리스크 점수 (0.0 ~ 1.0)
                "recommendations": list,  # 권장사항
            }
        """
        violations = []
        risk_score = 0.0
        recommendations = []

        # 텍스트 변환
        text = str(data) if isinstance(data, dict) else data

        # PII 검사
        if pii_check:
            pii_results = PIIClassifier.classify_pii(text)
            if len(pii_results) > 0:
                violations.append(
                    {
                        "type": "PII Detected",
                        "severity": "CRITICAL",
                        "count": len(pii_results),
                        "details": pii_results[:3],  # 처음 3개만 표시
                    }
                )
                risk_score += 0.4  # PII 감지는 큰 리스크
                recommendations.append("PII 데이터 마스킹 또는 암호화 필요")

        # 크기 검사
        text_size_mb = len(text.encode("utf-8")) / (1024 * 1024)
        if text_size_mb > size_limit_mb:
            violations.append(
                {
                    "type": "Size Limit Exceeded",
                    "severity": "MEDIUM",
                    "limit": f"{size_limit_mb}MB",
                    "actual": f"{text_size_mb:.2f}MB",
                }
            )
            risk_score += 0.2
            recommendations.append("파일 크기 제한 준수 필요")

        # 위험 키워드 검사
        DANGEROUS_PATTERNS = [
            r"(?:password|passwd|pwd)\s*[:=][\w']+",
            r"(?:secret|key|token)\s*[:=][\w']+",
            r"(?:api[_-]?key|apikey)\s*[:=][\w']+",
        ]

        for pattern in DANGEROUS_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                violations.append(
                    {
                        "type": "Sensitive Keyword",
                        "severity": "HIGH",
                        "keyword": match.group()[:20],
                        "context": text[max(0, match.start() - 20) : match.end() + 20],
                    }
                )
                risk_score += 0.3
                recommendations.append("민감 키워드 제거 필요")

        # 최종 판정
        passed = risk_score < 0.5  # 0.5 미만이면 통과

        if passed:
            logger.info(f"보안 게이트 통과: risk_score={risk_score:.2f}")
        else:
            logger.warning(f"보안 게이트 실패: risk_score={risk_score:.2f}")

        result = {
            "passed": passed,
            "violations": violations,
            "risk_score": min(risk_score, 1.0),
            "recommendations": recommendations,
        }

        return result

    @staticmethod
    def check_encryption_status(
        encrypted: bool, key_available: bool, algorithm: str
    ) -> dict[str, Any]:
        """
        암호화 상태 검증

        Args:
            encrypted: 암호화 여부
            key_available: 키 사용 가능 여부
            algorithm: 암호화 알고리즘

        Returns:
            암호화 상태 검증 결과
        """
        violations = []
        risk_score = 0.0

        if not encrypted:
            violations.append(
                {
                    "type": "Unencrypted Data",
                    "severity": "HIGH",
                    "message": "데이터가 암호화되지 않음",
                }
            )
            risk_score += 0.5

        if not key_available:
            violations.append(
                {
                    "type": "Key Unavailable",
                    "severity": "CRITICAL",
                    "message": "암호화 키가 없음",
                }
            )
            risk_score += 0.5

        if algorithm.lower() not in ["sha256", "sha512", "fernet"]:
            violations.append(
                {
                    "type": "Weak Algorithm",
                    "severity": "MEDIUM",
                    "message": f"약한 알고리즘 사용: {algorithm}",
                }
            )
            risk_score += 0.3

        passed = risk_score < 0.5

        if passed:
            logger.info("암호화 상태 검증 통과")
        else:
            logger.warning(f"암호화 상태 검증 실패: risk_score={risk_score:.2f}")

        result = {
            "passed": passed,
            "violations": violations,
            "risk_score": min(risk_score, 1.0),
            "algorithm": algorithm,
        }

        return result


# Convenience Functions
def classify_pii(text: str) -> list[dict[str, Any]]:
    """PII 식별 (편의 함수)"""
    return PIIClassifier.classify_pii(text)


def mask_pii(text: str, pii_results: list[dict[str, Any]]) -> str:
    """PII 마스킹 (편의 함수)"""
    return PIIClassifier.mask_pii(text, pii_results)


def has_pii(text: str) -> bool:
    """PII 포함 여부 확인 (편의 함수)"""
    return PIIClassifier.has_pii(text)


def check_data_security(
    data: str | dict[str, Any],
    pii_check: bool = True,
    size_limit_mb: int = 10,
) -> dict[str, Any]:
    """데이터 보안 검증 (편의 함수)"""
    return SecurityGate.check_data_security(data, pii_check, size_limit_mb)


def check_encryption_status(encrypted: bool, key_available: bool, algorithm: str) -> dict[str, Any]:
    """암호화 상태 검증 (편의 함수)"""
    return SecurityGate.check_encryption_status(encrypted, key_available, algorithm)


__all__ = [
    "SecurityLevel",
    "PIIType",
    "PIIClassifier",
    "SecurityGate",
    "classify_pii",
    "mask_pii",
    "has_pii",
    "check_data_security",
    "check_encryption_status",
]
