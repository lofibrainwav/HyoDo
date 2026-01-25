#!/usr/bin/env python3
"""
AFO 왕국 스마트 증분 품질 검사 시스템
변경된 파일만 검사하고 캐싱을 활용하여 실행 시간 극대화 단축
"""

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple


class SmartIncrementalChecker:
    """스마트 증분 품질 검사기"""

    def __init__(self) -> None:
        self.project_root = Path(__file__).parent.parent
        self.cache_dir = self.project_root / ".quality_cache"
        self.cache_file = self.cache_dir / "file_hashes.json"
        self.results_file = self.cache_dir / "last_results.json"

        self.cache_dir.mkdir(exist_ok=True)

    def get_file_hash(self, file_path: Path) -> str:
        """파일의 해시 계산"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def get_changed_files(self) -> Set[Path]:
        """Git을 통해 변경된 파일들 가져오기"""
        try:
            # Git으로 변경된 파일들 찾기
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only", "--", "*.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            # Staged 파일들
            staged_files = set()
            if result.returncode == 0:
                staged_files = {
                    self.project_root / f for f in result.stdout.strip().split("\n") if f
                }

            # Unstaged 변경 파일들
            result2 = subprocess.run(
                ["git", "diff", "--name-only", "--", "*.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            unstaged_files = set()
            if result2.returncode == 0:
                unstaged_files = {
                    self.project_root / f for f in result2.stdout.strip().split("\n") if f
                }

            # Untracked 파일들
            result3 = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard", "--", "*.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            untracked_files = set()
            if result3.returncode == 0:
                untracked_files = {
                    self.project_root / f for f in result3.stdout.strip().split("\n") if f
                }

            return (staged_files | unstaged_files | untracked_files) - {
                self.project_root / ""
            }  # 빈 문자열 제거

        except Exception as e:
            print(f"⚠️  Git 변경 감지 실패: {e}")
            return set()

    def load_cache(self) -> Dict[str, str]:
        """캐시된 파일 해시들 로드"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_cache(self, hashes: Dict[str, str]) -> None:
        """파일 해시들 캐시에 저장"""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(hashes, f, indent=2)
        except Exception as e:
            print(f"⚠️  캐시 저장 실패: {e}")

    def load_last_results(self) -> Dict[str, Tuple[bool, str]]:
        """이전 실행 결과 로드"""
        if self.results_file.exists():
            try:
                with open(self.results_file, "r") as f:
                    data = json.load(f)
                    return {k: tuple(v) for k, v in data.items()}
            except Exception:
                pass
        return {}

    def save_last_results(self, results: Dict[str, Tuple[bool, str]]) -> None:
        """실행 결과 저장"""
        try:
            with open(self.results_file, "w") as f:
                json.dump(results, f, indent=2)
        except Exception as e:
            print(f"⚠️  결과 저장 실패: {e}")

    def should_check_file(
        self, file_path: Path, current_hashes: Dict[str, str], changed_files: Set[Path]
    ) -> bool:
        """파일을 검사해야 하는지 결정"""
        if file_path in changed_files:
            return True

        # 캐시된 해시와 비교
        file_key = str(file_path.relative_to(self.project_root))
        current_hash = self.get_file_hash(file_path)
        cached_hash = current_hashes.get(file_key, "")

        return current_hash != cached_hash

    def run_incremental_checks(self, changed_files: List[str]) -> Dict[str, Tuple[bool, str]]:
        """증분 검사 실행"""

        print("🔍 [AFO] 스마트 증분 검사 시작...")
        start_time = time.time()

        # 변경된 파일들을 Path 객체로 변환
        changed_paths = {self.project_root / f for f in changed_files if f.strip()}
        changed_paths.discard(self.project_root / "")  # 빈 문자열 제거

        # 모든 Python 파일들 찾기 (코어 패키지만)
        all_py_files = set()
        core_dirs = ["packages/afo-core", "scripts"]

        for core_dir in core_dirs:
            core_path = self.project_root / core_dir
            if core_path.exists():
                for py_file in core_path.rglob("*.py"):
                    # 테스트와 레거시 제외
                    if not any(
                        part in py_file.parts for part in ["tests", "legacy", "__pycache__"]
                    ):
                        all_py_files.add(py_file)

        # 캐시 로드
        current_hashes = self.load_cache()
        last_results = self.load_last_results()

        # 검사할 파일들 결정
        files_to_check = set()
        for py_file in all_py_files:
            if self.should_check_file(py_file, current_hashes, changed_paths):
                files_to_check.add(py_file)

        print(f"📁 [AFO] 검사 대상 파일: {len(files_to_check)}개")

        if not files_to_check:
            print("✅ [AFO] 변경된 파일 없음 - 캐시된 결과 사용")
            return last_results

        # 증분 검사 실행 (변경된 파일만)
        results = {}

        # 1. Ruff 검사 (가장 빠름)
        if files_to_check:
            file_list = [str(f.relative_to(self.project_root)) for f in files_to_check]
            try:
                cmd = ["ruff", "check", "--fix", "--unsafe-fixes"] + file_list
                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                results["ruff"] = (
                    result.returncode == 0,
                    result.stdout + result.stderr,
                )
                print("✅ [AFO] Ruff 증분 검사 완료")
            except subprocess.TimeoutExpired:
                results["ruff"] = (False, "Timeout after 30 seconds")
                print("⏰ [AFO] Ruff 타임아웃")

        # 2. MyPy 검사 (변경된 파일만)
        try:
            file_args = [str(f.relative_to(self.project_root)) for f in files_to_check]

            if file_args:
                cmd = ["mypy"] + file_args
                result = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                results["mypy"] = (
                    result.returncode == 0,
                    result.stdout + result.stderr,
                )
                print("✅ [AFO] MyPy 증분 검사 완료")
            else:
                results["mypy"] = (True, "No files to check")
        except subprocess.TimeoutExpired:
            results["mypy"] = (False, "Timeout after 60 seconds")
            print("⏰ [AFO] MyPy 타임아웃")

        # 3. Pyright 검사 (전체 프로젝트지만 캐시 활용)
        try:
            result = subprocess.run(
                ["pyright", "--project", "pyproject.toml"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=45,
            )
            results["pyright"] = (result.returncode == 0, result.stdout + result.stderr)
            print("✅ [AFO] Pyright 증분 검사 완료")
        except subprocess.TimeoutExpired:
            results["pyright"] = (False, "Timeout after 45 seconds")
            print("⏰ [AFO] Pyright 타임아웃")

        # 캐시 업데이트
        new_hashes = {}
        for py_file in all_py_files:
            file_key = str(py_file.relative_to(self.project_root))
            new_hashes[file_key] = self.get_file_hash(py_file)

        self.save_cache(new_hashes)
        self.save_last_results(results)

        execution_time = time.time() - start_time
        print(f"⏱️  [AFO] 증분 검사 완료: {execution_time:.2f}초")

        return results


def main() -> None:
    """메인 실행 함수"""
    checker = SmartIncrementalChecker()

    # 변경된 파일들 받아오기
    changed_files = sys.argv[1:] if len(sys.argv) > 1 else []

    try:
        results = checker.run_incremental_checks(changed_files)

        # 결과 요약
        successful = sum(1 for success, _ in results.values() if success)
        total = len(results)

        print(f"\n📊 [AFO] 증분 검사 결과: {successful}/{total} 성공")

        # 실패 분석
        failures = [(name, output) for name, (success, output) in results.items() if not success]
        if failures:
            print("\n❌ 실패한 검사들:")
            for name, output in failures:
                print(f"  - {name}: {output[:200]}...")

        # 성공률 기반 종료
        success_rate = successful / total if total > 0 else 0
        sys.exit(0 if success_rate >= 0.7 else 1)  # 70% 이상 성공 시 통과

    except Exception as e:
        print(f"❌ [AFO] 증분 검사 시스템 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
