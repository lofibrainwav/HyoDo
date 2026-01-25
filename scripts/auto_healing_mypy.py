#!/usr/bin/env python3
"""
AFO 왕국 자율 치유 시스템: MyPy Purifier (관우 장군)

眞 (Truth): 타입 안전성 자동 수정
세종대왕 정신: "기존 기술을 실용적으로 흡수하여 왕국만의 철학을 주입"

작성일시: 2025년 12월 21일
작성자: 승상 (丞相) - AFO Kingdom
"""

from __future__ import annotations

import json
import logging
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


class MyPyPurifier:
    """
    관우(truth_guard) 장군: MyPy 오류 자동 수정 시스템

    眞 (Truth - 35%): 기술적 확실성 수호
    """

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self.errors: list[dict[str, Any]] = []
        self.fixed_count = 0
        self.total_errors = 0

    def collect_errors(self) -> list[dict[str, Any]]:
        """MyPy 오류 수집 (지피지기)"""
        logger.info("[眞] MyPy 오류 수집 시작...")

        try:
            result = subprocess.run(
                [
                    "mypy",
                    str(_PACKAGES_ROOT),
                    "--show-error-codes",
                    "--no-error-summary",
                ],
                capture_output=True,
                text=True,
                cwd=str(_AFO_ROOT),
                check=False,
            )

            errors: list[dict[str, Any]] = []

            # stderr와 stdout 모두 확인
            output = result.stdout + result.stderr

            for line in output.split("\n"):
                line = line.strip()
                if not line:
                    continue

                # MyPy 오류 형식: file:line: error: message [code]
                # 예: packages/afo-core/file.py:30: error: message [code]
                if ": error:" in line:
                    # packages/afo-core로 시작하는 라인만 처리
                    if "packages/afo-core" in line or str(_PACKAGES_ROOT) in line:
                        # 여러 가지 형식 처리
                        # 형식: file:line: error: message [code]
                        parts = line.split(":", 3)
                        if len(parts) >= 4:
                            file_path = parts[0]
                            try:
                                line_num = int(parts[1])
                                parts[2].strip()  # "error"
                                error_msg = parts[3].strip()

                                # 오류 코드 추출
                                error_code = ""
                                if "[" in error_msg and "]" in error_msg:
                                    code_start = error_msg.rindex("[")
                                    code_end = error_msg.rindex("]")
                                    error_code = error_msg[code_start + 1 : code_end]
                                    error_msg = error_msg[:code_start].strip()

                                errors.append(
                                    {
                                        "file": file_path,
                                        "line": line_num,
                                        "message": error_msg,
                                        "code": error_code,
                                    }
                                )
                            except (ValueError, IndexError) as e:
                                # 파싱 실패 시 전체 라인 저장
                                logger.debug("[眞] 파싱 실패: %s - %s", line, e)
                                continue

            self.total_errors = len(errors)
            logger.info(f"[眞] 총 {self.total_errors}개 오류 수집 완료")
            return errors

        except FileNotFoundError:
            logger.exception("[眞] MyPy가 설치되지 않았습니다. 'pip install mypy' 실행 필요")
            return []
        except Exception as e:
            logger.exception("[眞] 오류 수집 실패: %s", e)
            return []

    def classify_errors(self, errors: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """오류 유형별 분류"""
        classified: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for error in errors:
            code = error.get("code", "unknown")
            classified[code].append(error)

        logger.info(f"[眞] 오류 분류 완료: {len(classified)}개 유형")
        for code, errs in sorted(classified.items(), key=lambda x: len(x[1]), reverse=True):
            logger.info(f"  - {code}: {len(errs)}개")

        return dict(classified)

    def analyze_fixable_errors(
        self, classified: dict[str, list[dict[str, Any]]]
    ) -> list[dict[str, Any]]:
        """자동 수정 가능한 오류 분석"""
        fixable_patterns = {
            "unused-ignore": 'Unused "type: ignore"',
            "unreachable": "Statement is unreachable",
            "no-redef": "Name.*already defined",
        }

        fixable: list[dict[str, Any]] = []

        for code, errors in classified.items():
            for error in errors:
                msg = error.get("message", "")
                for pattern, description in fixable_patterns.items():
                    if pattern in code.lower() or description.lower() in msg.lower():
                        error["fixable"] = True
                        error["fix_type"] = pattern
                        fixable.append(error)
                        break

        logger.info(f"[眞] 자동 수정 가능: {len(fixable)}개")
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

    def execute_fixes(self, plan: dict[str, Any]) -> dict[str, Any]:
        """수정 실행 (WET_RUN)"""
        if self.dry_run:
            logger.info("[眞] DRY_RUN 모드: 수정 계획만 생성")
            return {"status": "dry_run", "plan": plan}

        logger.info("[眞] WET_RUN 모드: 실제 수정 시작...")
        results: dict[str, Any] = {
            "fixed_files": [],
            "failed_files": [],
            "total_fixed": 0,
        }

        for fix in plan["fixes"]:
            file_path = Path(fix["file"])
            if not file_path.exists():
                logger.warning("[眞] 파일 없음: %s", file_path)
                continue

            try:
                # 파일 읽기
                content = file_path.read_text(encoding="utf-8")
                lines = content.split("\n")

                # 수정 적용 (간단한 패턴만)
                modified = False
                for error in fix["errors"]:
                    line_idx = error["line"] - 1
                    if line_idx < len(lines):
                        original = lines[line_idx]
                        # Unused type: ignore 제거
                        if "unused-ignore" in error.get("fix_type", ""):
                            lines[line_idx] = original.replace("  # type: ignore", "").replace(
                                "  # type: ignore[", "  # type: ignore["
                            )
                            modified = True

                if modified:
                    # 파일 쓰기
                    file_path.write_text("\n".join(lines), encoding="utf-8")
                    results["fixed_files"].append(str(file_path))
                    results["total_fixed"] += len(fix["errors"])
                    logger.info(f"[眞] 수정 완료: {file_path} ({len(fix['errors'])}개)")

            except Exception as e:
                logger.exception("[眞] 수정 실패: %s - %s", file_path, e)
                results["failed_files"].append({"file": str(file_path), "error": str(e)})

        return results

    def verify_fixes(self) -> dict[str, Any]:
        """수정 검증"""
        logger.info("[眞] 수정 검증 시작...")

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
        logger.info("[眞] 관우(truth_guard) 장군: MyPy Purifier 작전 시작")
        logger.info("=" * 80)

        # Step 1: 오류 수집
        errors = self.collect_errors()
        if not errors:
            return {"status": "no_errors", "message": "MyPy 오류가 없습니다."}

        # Step 2: 오류 분류
        classified = self.classify_errors(errors)

        # Step 3: 수정 가능한 오류 분석
        fixable = self.analyze_fixable_errors(classified)

        # Step 4: 수정 계획 생성
        plan = self.generate_fix_plan(fixable)

        # Step 5: 수정 실행
        results = self.execute_fixes(plan)

        # Step 6: 검증
        if not self.dry_run:
            verification = self.verify_fixes()
            results["verification"] = verification

        logger.info("=" * 80)
        logger.info("[眞] 관우(truth_guard) 장군: 작전 완료")
        logger.info("=" * 80)

        return {
            "status": "success",
            "plan": plan,
            "results": results,
        }


def main() -> int:
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="AFO 왕국 MyPy Purifier (관우 장군)")
    parser.add_argument(
        "--dry-run", action="store_true", default=True, help="DRY_RUN 모드 (기본값)"
    )
    parser.add_argument("--wet-run", action="store_true", help="WET_RUN 모드 (실제 수정)")

    args = parser.parse_args()

    dry_run = not args.wet_run

    purifier = MyPyPurifier(dry_run=dry_run)
    result = purifier.run()

    # 결과 출력
    print("\n" + "=" * 80)
    print("결과 요약:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
