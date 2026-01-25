#!/usr/bin/env python3
"""
AFO 왕국 자율 치유 시스템: Ruff Purifier (조운 장군)

美 (Beauty): 코드 스타일 자동 수정
세종대왕 정신: "기존 기술을 실용적으로 흡수하여 왕국만의 철학을 주입"

작성일시: 2025년 12월 21일
작성자: 승상 (丞相) - AFO Kingdom
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# AFO 왕국 루트 경로
_AFO_ROOT = Path(__file__).parent.parent
_PACKAGES_ROOT = _AFO_ROOT / "packages" / "afo-core"


class RuffPurifier:
    """
    조운(beauty_craft) 장군: Ruff 오류 자동 수정 시스템

    美 (Beauty - 20%): 구조적 우아함 수호
    """

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self.errors: list[dict[str, Any]] = []
        self.fixed_count = 0
        self.total_errors = 0

    def collect_errors(self) -> list[dict[str, Any]]:
        """Ruff 오류 수집 (지피지기)"""
        logger.info("[美] Ruff 오류 수집 시작...")

        try:
            # 텍스트 형식으로 먼저 시도
            result = subprocess.run(
                ["ruff", "check", str(_PACKAGES_ROOT)],
                capture_output=True,
                text=True,
                cwd=str(_AFO_ROOT),
                check=False,
            )

            errors: list[dict[str, Any]] = []
            output = result.stdout + result.stderr

            # ANSI 색상 코드 제거
            ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
            output = ansi_escape.sub("", output)

            # Ruff 출력 형식 파싱
            # 형식: "F401 `module` imported but unused"
            #       "--> packages/afo-core/file.py:line:col"
            current_file = ""
            current_code = ""
            current_message = ""

            lines = output.split("\n")
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue

                # "Found X errors" 라인은 건너뛰기
                if line.startswith("Found"):
                    i += 1
                    continue

                # 코드 라인 (예: "F401 `module` imported but unused")
                # 코드 형식: F401, SIM117, B904 등 (문자 + 숫자)
                # ANSI 코드 제거 후 첫 번째 단어가 코드인지 확인
                if line:
                    parts = line.split(None, 1)  # 첫 번째 공백으로만 분리
                    if len(parts) >= 1:
                        potential_code = parts[0]
                        # 코드 형식 확인 (예: F401, SIM117, B904)
                        # 패턴: 문자로 시작하고 숫자가 포함 (최소 3자)
                        if len(potential_code) >= 3:
                            # 첫 문자가 알파벳이고, 나머지에 숫자가 포함
                            if potential_code[0].isalpha() and any(
                                c.isdigit() for c in potential_code[1:]
                            ):
                                current_code = potential_code
                                current_message = parts[1] if len(parts) > 1 else ""

                # 파일 위치 라인 (예: "--> packages/afo-core/file.py:line:col")
                if line.startswith("-->"):
                    # 형식: "--> file:line:col"
                    rest = line.replace("-->", "").strip()
                    if ":" in rest and ("packages/afo-core" in rest or str(_PACKAGES_ROOT) in rest):
                        parts = rest.split(":")
                        if len(parts) >= 2:
                            file_path = parts[0].strip()
                            try:
                                line_num = int(parts[1].strip())
                                current_file = file_path

                                # 현재 코드와 메시지가 있으면 오류 추가
                                if current_code and current_file:
                                    errors.append(
                                        {
                                            "file": current_file,
                                            "line": line_num,
                                            "code": current_code,
                                            "message": current_message,
                                        }
                                    )
                                    # 다음 오류를 위해 초기화
                                    current_code = ""
                                    current_message = ""
                            except (ValueError, IndexError):
                                pass

                i += 1

            self.total_errors = len(errors)
            logger.info(f"[美] 총 {self.total_errors}개 오류 수집 완료")

            if self.total_errors == 0 and result.returncode != 0:
                # 오류가 있는데 파싱 실패한 경우
                logger.warning(f"[美] Ruff 종료 코드: {result.returncode}")
                logger.warning(f"[美] 출력 샘플: {output[:500]}")

            return errors

            self.total_errors = len(errors)
            logger.info(f"[美] 총 {self.total_errors}개 오류 수집 완료")
            return errors

        except FileNotFoundError:
            logger.exception("[美] Ruff가 설치되지 않았습니다. 'pip install ruff' 실행 필요")
            return []
        except Exception as e:
            logger.exception("[美] 오류 수집 실패: %s", e)
            return []

    def classify_errors(self, errors: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """오류 유형별 분류"""
        classified: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for error in errors:
            code = error.get("code", "unknown")
            classified[code].append(error)

        logger.info(f"[美] 오류 분류 완료: {len(classified)}개 유형")
        for code, errs in sorted(classified.items(), key=lambda x: len(x[1]), reverse=True):
            logger.info(f"  - {code}: {len(errs)}개")

        return dict(classified)

    def analyze_fixable_errors(
        self, classified: dict[str, list[dict[str, Any]]]
    ) -> list[dict[str, Any]]:
        """자동 수정 가능한 오류 분석"""
        # Ruff 자동 수정 가능한 코드 목록
        auto_fixable_codes = {
            "W293",  # blank-line-with-whitespace
            "F401",  # unused-import (일부)
            "SIM117",  # multiple-with-statements (일부)
            "B904",  # raise-without-from (일부)
        }

        fixable: list[dict[str, Any]] = []

        for errors in classified.values():
            for error in errors:
                error_code = error.get("code", "").upper()
                if error_code in auto_fixable_codes:
                    error["fixable"] = True
                    error["fix_type"] = error_code
                    fixable.append(error)
                elif "unused" in error.get("message", "").lower():
                    error["fixable"] = True
                    error["fix_type"] = "unused-import"
                    fixable.append(error)

        logger.info(f"[美] 자동 수정 가능: {len(fixable)}개")
        return fixable

    def generate_fix_plan(self, fixable: list[dict[str, Any]]) -> dict[str, Any]:
        """수정 계획 생성"""
        plan: dict[str, Any] = {
            "total_errors": self.total_errors,
            "fixable_count": len(fixable),
            "fixes": [],
        }

        # 파일별로 그룹화
        by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for error in fixable:
            by_file[error["file"]].append(error)

        for file_path, errors in by_file.items():
            plan["fixes"].append(
                {
                    "file": file_path,
                    "errors": errors,
                    "count": len(errors),
                }
            )

        return plan

    def execute_auto_fix(self) -> dict[str, Any]:
        """Ruff 자동 수정 실행"""
        if self.dry_run:
            logger.info("[美] DRY_RUN 모드: 자동 수정 시뮬레이션")
            return {"status": "dry_run", "message": "자동 수정 시뮬레이션 완료"}

        logger.info("[美] WET_RUN 모드: Ruff 자동 수정 시작...")

        try:
            # Ruff 자동 수정 실행
            result = subprocess.run(
                ["ruff", "check", str(_PACKAGES_ROOT), "--fix"],
                capture_output=True,
                text=True,
                cwd=str(_AFO_ROOT),
                check=False,
            )

            fixed_count = 0
            if "fixed" in result.stdout.lower() or result.returncode == 0:
                # 수정된 항목 수 추출
                for line in result.stdout.split("\n"):
                    if "fixed" in line.lower():
                        # "Found X errors (Y fixed)" 형식
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if "fixed" in part.lower() and i > 0:
                                try:
                                    fixed_count = int(parts[i - 1])
                                    break
                                except (ValueError, IndexError):
                                    pass

            logger.info("[美] Ruff 자동 수정 완료: %s개", fixed_count)

            return {
                "status": "success",
                "fixed_count": fixed_count,
                "output": result.stdout,
            }

        except Exception as e:
            logger.exception("[美] 자동 수정 실패: %s", e)
            return {"status": "error", "message": str(e)}

    def verify_fixes(self) -> dict[str, Any]:
        """수정 검증"""
        logger.info("[美] 수정 검증 시작...")

        errors_after = self.collect_errors()
        reduction = self.total_errors - len(errors_after)

        return {
            "errors_before": self.total_errors,
            "errors_after": len(errors_after),
            "reduction": reduction,
            "reduction_percent": (
                (reduction / self.total_errors * 100) if self.total_errors > 0 else 0
            ),
        }

    def run(self) -> dict[str, Any]:
        """전체 프로세스 실행"""
        logger.info("=" * 80)
        logger.info("[美] 조운(beauty_craft) 장군: Ruff Purifier 작전 시작")
        logger.info("=" * 80)

        # Step 1: 오류 수집
        errors = self.collect_errors()
        if not errors:
            return {"status": "no_errors", "message": "Ruff 오류가 없습니다."}

        # Step 2: 오류 분류
        classified = self.classify_errors(errors)

        # Step 3: 수정 가능한 오류 분석
        fixable = self.analyze_fixable_errors(classified)

        # Step 4: 수정 계획 생성
        plan = self.generate_fix_plan(fixable)

        # Step 5: 자동 수정 실행
        auto_fix_result = self.execute_auto_fix()

        # Step 6: 검증
        if not self.dry_run:
            verification = self.verify_fixes()
            auto_fix_result["verification"] = verification

        logger.info("=" * 80)
        logger.info("[美] 조운(beauty_craft) 장군: 작전 완료")
        logger.info("=" * 80)

        return {
            "status": "success",
            "plan": plan,
            "auto_fix": auto_fix_result,
        }


def main() -> int:
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="AFO 왕국 Ruff Purifier (조운 장군)")
    parser.add_argument(
        "--dry-run", action="store_true", default=True, help="DRY_RUN 모드 (기본값)"
    )
    parser.add_argument("--wet-run", action="store_true", help="WET_RUN 모드 (실제 수정)")

    args = parser.parse_args()

    dry_run = not args.wet_run

    purifier = RuffPurifier(dry_run=dry_run)
    result = purifier.run()

    # 결과 출력
    print("\n" + "=" * 80)
    print("결과 요약:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
