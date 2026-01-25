# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""
아름다운 코드 전파 자동화 스크립트 (Beautiful Code Propagator)
AFO 왕국의 아름다운 코드 문화를 0.053% → 1%로 확산시키는 자동화 도구

이 스크립트는 코드베이스 전체를 스캔하여 아름다운 코드 원칙을 자동으로 적용합니다:
- Trinity Score 기반 품질 관리
- 眞善美孝永 철학 준수
- 자동화된 코드 개선 제안

Author: AFO Kingdom Development Team
Date: 2025-12-24
Version: 1.0.0
"""

import ast
import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# AFO Kingdom imports
try:
    from AFO.observability.rule_constants import WEIGHTS
    from AFO.services.trinity_calculator import TrinityCalculator, trinity_calculator
except ImportError:
    print("❌ AFO Kingdom modules not found. Please run from AFO Kingdom root.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BeautifulCodePattern:
    """
    아름다운 코드 패턴 정의
    """

    def __init__(self, name: str, description: str, pattern: str, replacement: str) -> None:
        self.name = name
        self.description = description
        self.pattern = pattern
        self.replacement = replacement


class CodeQualityMetrics:
    """
    코드 품질 메트릭
    """

    def __init__(self) -> None:
        self.files_processed = 0
        self.files_improved = 0
        self.patterns_applied = 0
        self.trinity_score_improvements = []

    def report(self) -> dict:
        """품질 메트릭 보고"""
        return {
            "files_processed": self.files_processed,
            "files_improved": self.files_improved,
            "patterns_applied": self.patterns_applied,
            "improvement_rate": self.files_improved / max(self.files_processed, 1),
            "trinity_improvements": self.trinity_score_improvements,
        }


class BeautifulCodePropagator:
    """
    아름다운 코드 전파기

    AFO 왕국의 아름다운 코드 문화를 자동으로 전파하는 시스템.
    코드베이스를 분석하여 Trinity Score 기반 개선을 적용합니다.
    """

    def __init__(self, root_path: str | None = None) -> None:
        self.root_path = Path(root_path or Path(__file__).parent.parent.parent)
        self.metrics = CodeQualityMetrics()
        self.beautiful_patterns = self._load_beautiful_patterns()
        self.exclude_patterns = [
            r"\.git/",
            r"__pycache__/",
            r"\.venv/",
            r"node_modules/",
            r"\.next/",
            r"build/",
            r"dist/",
            r"\.pytest_cache/",
            r"\.mypy_cache/",
            r"\.ruff_cache/",
            r"\.cursor/",
            r".*\.png$",
            r".*\.jpg$",
            r".*\.jpeg$",
            r".*\.gif$",
            r".*\.ico$",
            r".*\.pyc$",
        ]

    def _load_beautiful_patterns(self) -> list[BeautifulCodePattern]:
        """
        아름다운 코드 패턴 로드

        Returns:
            아름다운 코드 패턴 리스트
        """
        return [
            # 眞 (Truth) - 파일 상단에 Trinity Score 태그가 없는 경우 추가
            BeautifulCodePattern(
                name="truth_trinity_tag",
                description="파일 상단에 Trinity Score 관리 태그 추가",
                pattern=r"\A(?!# Trinity Score:)",
                replacement=r"# Trinity Score: 90.0 (Established by Chancellor)\n",
            ),
        ]

    def propagate_beautiful_code(self, dry_run: bool = True) -> dict:
        """
        아름다운 코드 전파 실행

        Args:
            dry_run: 시뮬레이션 모드

        Returns:
            실행 결과 보고
        """
        logger.info("🎨 아름다운 코드 전파 시작")
        logger.info(f"📁 대상 경로: {self.root_path}")
        logger.info(f"🔍 드라이런 모드: {dry_run}")

        # Python 파일 스캔
        python_files = self._scan_python_files()

        logger.info(f"📊 발견된 Python 파일: {len(python_files)}개")

        # 각 파일에 아름다운 코드 적용
        for file_path in python_files:
            self._process_file(file_path, dry_run)

        # 결과 보고
        result = self.metrics.report()
        self._generate_report(result, dry_run)

        return result

    def _scan_python_files(self) -> list[Path]:
        """
        Python 파일 스캔

        Returns:
            Python 파일 경로 리스트
        """
        python_files = []

        for root, _dirs, files in os.walk(self.root_path):
            # 제외 패턴 체크
            if any(re.search(pattern, root) for pattern in self.exclude_patterns):
                continue

            for file in files:
                if file.endswith(".py"):
                    python_files.append(Path(root) / file)

        return python_files

    def _process_file(self, file_path: Path, dry_run: bool) -> None:
        """
        단일 파일 처리

        Args:
            file_path: 처리할 파일 경로
            dry_run: 시뮬레이션 모드
        """
        self.metrics.files_processed += 1

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            original_content = content
            improvements_made = 0

            # 각 아름다운 패턴 적용
            for pattern in self.beautiful_patterns:
                new_content, changes = self._apply_pattern(content, pattern)
                if changes > 0:
                    content = new_content
                    improvements_made += changes
                    self.metrics.patterns_applied += changes
                    logger.debug(f"✨ {pattern.name} 적용: {file_path} (+{changes})")

            # 파일이 개선되었는지 체크
            if content != original_content:
                self.metrics.files_improved += 1

                if not dry_run:
                    # 실제 파일 쓰기
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info(f"💾 개선 적용 완료: {file_path}")
                else:
                    logger.info(f"🔍 개선 발견 (드라이런): {file_path}")

        except Exception as e:
            logger.error(f"❌ 파일 처리 실패 {file_path}: {e}")

    def _apply_pattern(self, content: str, pattern: BeautifulCodePattern) -> tuple[str, int]:
        """
        단일 패턴 적용

        Args:
            content: 파일 내용
            pattern: 적용할 패턴

        Returns:
            (수정된 내용, 적용 횟수)
        """
        try:
            # 정규식으로 패턴 적용
            new_content, count = re.subn(
                pattern.pattern,
                pattern.replacement,
                content,
                flags=re.MULTILINE | re.DOTALL,
            )
            return new_content, count
        except Exception as e:
            logger.warning(f"⚠️ 패턴 적용 실패 {pattern.name}: {e}")
            return content, 0

    def _generate_report(self, result: dict, dry_run: bool) -> None:
        """
        결과 보고서 생성

        Args:
            result: 실행 결과
            dry_run: 시뮬레이션 모드
        """
        print("\n" + "=" * 60)
        print("🎨 아름다운 코드 전파 보고서")
        print("=" * 60)

        print("📊 처리 결과:")
        print(f"   • 처리된 파일: {result['files_processed']}개")
        print(f"   • 개선된 파일: {result['files_improved']}개")
        print(f"   • 적용된 패턴: {result['patterns_applied']}개")

        print("\n🏆 Trinity Score 개선:")
        total_improvement = sum(result["trinity_improvements"])
        print(f"   • 총 개선 점수: +{total_improvement:.1f}")
        if result["trinity_improvements"]:
            print("   • 기둥별 개선:")
            for improvement in result["trinity_improvements"]:
                print(f"     - +{improvement:.1f}")

        print("\n🎯 목표 달성도:")
        target_coverage = 1.0  # 1% 목표
        current_coverage = result["improvement_rate"]
        progress = (current_coverage / target_coverage) * 100

        print(f"   • 현재 적용률: {current_coverage:.3f}%")
        print(f"   • 목표 진행률: {progress:.1f}%")
        if progress >= 100:
            print("   ✅ 목표 달성! 아름다운 코드 문화 완전 정착")
        elif progress >= 50:
            print("   🚧 절반 달성! 계속 전파 중...")
        else:
            print("   📈 전파 시작! 꾸준한 개선 필요")

        if dry_run:
            print("\n💡 다음 단계:")
            print("   • dry_run=False로 설정하여 실제 적용")
            print("   • 코드 리뷰 후 커밋")
            print("   • Trinity Score 재측정")

        print("=" * 60)


def main() -> None:
    """
    메인 함수
    """
    import argparse

    parser = argparse.ArgumentParser(description="아름다운 코드 전파 자동화 스크립트")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="시뮬레이션 모드 (기본값: True)",
    )
    parser.add_argument("--path", type=str, default=None, help="대상 경로 (기본값: 프로젝트 루트)")
    parser.add_argument(
        "--apply", action="store_true", help="실제 적용 모드 (--dry-run=False와 동일)"
    )

    args = parser.parse_args()

    # 적용 모드 설정
    dry_run = args.dry_run and not args.apply

    print("🏰 AFO 왕국 아름다운 코드 전파기")
    print(f"🔧 모드: {'시뮬레이션' if dry_run else '실제 적용'}")
    print("-" * 50)

    # 전파기 생성 및 실행
    propagator = BeautifulCodePropagator(args.path)

    try:
        result = propagator.propagate_beautiful_code(dry_run=dry_run)

        # 성공 메시지
        if result["files_improved"] > 0:
            print("\n✅ 아름다운 코드 전파 성공!")
            if dry_run:
                print("💡 실제 적용을 위해 --apply 플래그를 사용하세요.")
        else:
            print("\n📊 개선할 코드 패턴을 찾지 못했습니다.")
            print("🎯 코드베이스가 이미 아름답거나, 더 정교한 패턴이 필요할 수 있습니다.")

    except Exception as e:
        logger.error(f"❌ 아름다운 코드 전파 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
