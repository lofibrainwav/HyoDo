#!/usr/bin/env python3
"""
SSOT 드리프트 모니터링 시스템 (Single Source of Truth)

AFO Kingdom의 SSOT 파일들을 실시간으로 모니터링하여
드리프트(불일치)를 감지하고 경고하는 시스템입니다.

Trinity Score: 眞 (Truth) - SSOT 무결성 보장
"""

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SSOTMonitor:
    """
    SSOT 드리프트 모니터링 시스템

    핵심 기능:
    - SSOT 파일들의 해시 기반 무결성 검증
    - 드리프트 감지 및 보고
    - 자동 복구 제안
    - 감사 로그 기록
    """

    def __init__(self, ssot_dir: Optional[Path] = None) -> None:
        """
        SSOT 모니터 초기화

        Args:
            ssot_dir: SSOT 파일들이 위치한 기본 디렉토리
        """
        self.ssot_dir = ssot_dir or Path.cwd()
        self.baseline_file = self.ssot_dir / ".ssot_baseline.json"
        self.audit_log = self.ssot_dir / "docs" / "ssot_audit.log"

        # 핵심 SSOT 파일들 정의
        self.core_ssot_files = {
            "docs/AFO_FINAL_SSOT.md": "메인 SSOT 문서",
            "docs/AFO_ROYAL_LIBRARY.md": "로열 라이브러리",
            "docs/AFO_SSOT_CORE_DEFINITIONS.md": "SSOT 코어 정의",
            "packages/trinity-os/TRINITY_OS_PERSONAS.yaml": "Trinity OS 페르소나 정의",
            "pyproject.toml": "프로젝트 설정 (루트)",
            "packages/afo-core/pyproject.toml": "AFO 코어 설정",
        }

        # 선택적 SSOT 파일들 (존재하는 경우만 모니터링)
        self.optional_ssot_files = {
            "packages/trinity-os/TRINITY_OS_MASTER_DOCUMENT.md": "Trinity OS 마스터 문서",
            "docs/TRINITY_MANIFEST.md": "Trinity 매니페스트",
        }

        # 베이스라인 해시 로드
        self.baseline_hashes = self._load_baseline()

    def _load_baseline(self) -> Dict[str, str]:
        """베이스라인 해시값들 로드"""
        if self.baseline_file.exists():
            try:
                with open(self.baseline_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"베이스라인 파일 로드 실패: {e}")
                return {}
        return {}

    def _save_baseline(self, hashes: Dict[str, str]) -> None:
        """베이스라인 해시값들 저장"""
        try:
            with open(self.baseline_file, "w", encoding="utf-8") as f:
                json.dump(hashes, f, indent=2, ensure_ascii=False)
            logger.info(f"베이스라인 저장됨: {self.baseline_file}")
        except Exception as e:
            logger.error(f"베이스라인 저장 실패: {e}")

    def _calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """파일의 SHA256 해시 계산"""
        try:
            if not file_path.exists():
                return None

            with open(file_path, "rb") as f:
                content = f.read()

            # 파일 내용의 해시 계산
            return hashlib.sha256(content).hexdigest()

        except Exception as e:
            logger.error(f"해시 계산 실패 {file_path}: {e}")
            return None

    def scan_ssot_files(self) -> Dict[str, Dict[str, str]]:
        """
        모든 SSOT 파일들을 스캔하여 현재 상태 반환

        Returns:
            파일별 상태 정보 딕셔너리
        """
        results = {}

        # 핵심 SSOT 파일들 스캔
        for file_path, description in self.core_ssot_files.items():
            full_path = self.ssot_dir / file_path
            current_hash = self._calculate_file_hash(full_path)

            results[file_path] = {
                "description": description,
                "exists": full_path.exists(),
                "current_hash": current_hash,
                "baseline_hash": self.baseline_hashes.get(file_path),
                "is_core": True,
            }

        # 선택적 SSOT 파일들 스캔
        for file_path, description in self.optional_ssot_files.items():
            full_path = self.ssot_dir / file_path
            if full_path.exists():
                current_hash = self._calculate_file_hash(full_path)

                results[file_path] = {
                    "description": description,
                    "exists": True,
                    "current_hash": current_hash,
                    "baseline_hash": self.baseline_hashes.get(file_path),
                    "is_core": False,
                }

        return results

    def check_drift(self) -> Dict[str, List[str]]:
        """
        SSOT 드리프트 감지

        Returns:
            드리프트된 파일들의 카테고리별 목록
        """
        scan_results = self.scan_ssot_files()
        drifted_files = []
        missing_files = []
        new_files = []

        for file_path, info in scan_results.items():
            if not info["exists"]:
                if info["is_core"]:
                    missing_files.append(file_path)
                continue

            current_hash = info["current_hash"]
            baseline_hash = info["baseline_hash"]

            if baseline_hash is None:
                # 베이스라인이 없는 새 파일
                new_files.append(file_path)
            elif current_hash != baseline_hash:
                # 해시가 변경된 파일 (드리프트)
                drifted_files.append(file_path)

        return {
            "drifted": drifted_files,
            "missing": missing_files,
            "new": new_files,
        }

    def establish_baseline(self, force: bool = False) -> bool:
        """
        현재 SSOT 파일들의 상태를 베이스라인으로 설정

        Args:
            force: 강제 베이스라인 설정 (기존 베이스라인 덮어쓰기)

        Returns:
            성공 여부
        """
        # 드리프트 확인
        drift_check = self.check_drift()

        if not force and (drift_check["drifted"] or drift_check["missing"]):
            logger.error("드리프트가 감지되어 베이스라인 설정 불가")
            logger.error(f"드리프트된 파일들: {drift_check['drifted']}")
            logger.error(f"누락된 파일들: {drift_check['missing']}")
            return False

        # 현재 해시들을 계산하여 베이스라인 설정
        scan_results = self.scan_ssot_files()
        new_baseline = {}

        for file_path, info in scan_results.items():
            if info["exists"] and info["current_hash"]:
                new_baseline[file_path] = info["current_hash"]

        self.baseline_hashes = new_baseline
        self._save_baseline(new_baseline)

        logger.info(f"SSOT 베이스라인 설정 완료: {len(new_baseline)}개 파일")
        return True

    def generate_report(self) -> str:
        """현재 SSOT 상태에 대한 상세 보고서 생성"""
        drift_check = self.check_drift()
        scan_results = self.scan_ssot_files()

        report_lines = []
        report_lines.append("🔍 AFO Kingdom SSOT 드리프트 모니터링 보고서")
        report_lines.append("=" * 60)
        report_lines.append(f"생성 시각: {datetime.now(UTC).isoformat()}")
        report_lines.append("")

        # 드리프트 요약
        report_lines.append("📊 드리프트 요약:")
        report_lines.append(f"  • 드리프트된 파일: {len(drift_check['drifted'])}개")
        report_lines.append(f"  • 누락된 파일: {len(drift_check['missing'])}개")
        report_lines.append(f"  • 신규 파일: {len(drift_check['new'])}개")
        report_lines.append("")

        # 상태별 상세 정보
        if drift_check["drifted"]:
            report_lines.append("🚨 드리프트된 파일들:")
            for file_path in drift_check["drifted"]:
                info = scan_results[file_path]
                report_lines.append(f"  • {file_path}")
                report_lines.append(f"    설명: {info['description']}")
                report_lines.append(f"    현재 해시: {info['current_hash'][:16]}...")
            report_lines.append("")

        if drift_check["missing"]:
            report_lines.append("❌ 누락된 파일들:")
            for file_path in drift_check["missing"]:
                info = scan_results[file_path]
                report_lines.append(f"  • {file_path} ({info['description']})")
            report_lines.append("")

        if drift_check["new"]:
            report_lines.append("🆕 신규 파일들:")
            for file_path in drift_check["new"]:
                info = scan_results[file_path]
                report_lines.append(f"  • {file_path} ({info['description']})")
            report_lines.append("")

        # 전체 파일 상태
        report_lines.append("📁 전체 SSOT 파일 상태:")
        for file_path, info in scan_results.items():
            status = "✅" if info["exists"] else "❌"
            drift_status = ""
            if info["exists"] and info["baseline_hash"]:
                if info["current_hash"] != info["baseline_hash"]:
                    drift_status = " (드리프트)"
                else:
                    drift_status = " (정상)"

            report_lines.append(f"  {status} {file_path}{drift_status}")
            report_lines.append(f"      {info['description']}")

        return "\n".join(report_lines)


def main() -> None:
    """CLI 인터페이스"""
    import argparse

    parser = argparse.ArgumentParser(description="AFO Kingdom SSOT 드리프트 모니터링")
    parser.add_argument("--check", action="store_true", help="드리프트 체크")
    parser.add_argument("--baseline", action="store_true", help="베이스라인 설정")
    parser.add_argument("--report", action="store_true", help="상세 보고서 출력")
    parser.add_argument("--force", action="store_true", help="강제 베이스라인 설정")

    args = parser.parse_args()

    monitor = SSOTMonitor()

    if args.check:
        drift = monitor.check_drift()
        if drift["drifted"] or drift["missing"]:
            print("🚨 SSOT 드리프트 감지됨!")
            print(f"드리프트: {drift['drifted']}")
            print(f"누락: {drift['missing']}")
            return 1
        else:
            print("✅ SSOT 상태 정상")
            return 0

    elif args.baseline:
        success = monitor.establish_baseline(force=args.force)
        return 0 if success else 1

    elif args.report:
        print(monitor.generate_report())
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit(main())
