#!/usr/bin/env python3
"""
AFO Kingdom - System Information Validator
시스템 정보 정확한 파악을 위한 검증 스크립트

Purpose: 정확한 환경 정보 수집 및 검증 (SSOT 준수)
Author: AFO Kingdom 승상
Date: 2026-01-12

SSOT 준수:
- Python 인터프리터: python3 단일화 (docs/AFO_SSOT_CORE_DEFINITIONS.md)
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class SystemInfoValidator:
    """시스템 정보 검증 및 수집 클래스"""

    def __init__(self) -> None:
        self.project_root = Path(__file__).parent.parent
        self.info = {}

    def run_command(self, cmd: str, shell: bool = False) -> Optional[str]:
        """명령어 실행 및 결과 반환"""
        try:
            result = subprocess.run(
                cmd if shell else cmd.split(),
                shell=shell,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Error: {result.stderr.strip()}"
        except Exception as e:
            return f"Exception: {str(e)}"

    def get_python_versions(self) -> Dict[str, str]:
        """Python 버전 정보 수집"""
        versions = {}

        # python 명령어 버전
        python_version = self.run_command("python --version")
        versions["python"] = python_version or "Not found"

        # python3 명령어 버전
        python3_version = self.run_command("python3 --version")
        versions["python3"] = python3_version or "Not found"

        # pip 버전
        pip_version = self.run_command("pip --version")
        versions["pip"] = pip_version or "Not found"

        # poetry 버전
        poetry_version = self.run_command("poetry --version")
        versions["poetry"] = poetry_version or "Not found"

        return versions

    def get_system_info(self) -> Dict[str, Any]:
        """시스템 기본 정보 수집"""
        info = {
            "os": sys.platform,
            "architecture": sys.maxsize > 2**32 and "64bit" or "32bit",
            "python_executable": sys.executable,
            "python_path": sys.path[:3],  # 처음 3개만
            "working_directory": str(self.project_root),
            "user": os.environ.get("USER", "Unknown"),
        }
        return info

    def get_project_info(self) -> Dict[str, Any]:
        """프로젝트 관련 정보 수집"""
        info = {}

        # 파일 수량
        try:
            py_files = len(list(self.project_root.rglob("*.py")))
            info["python_files"] = py_files
        except:
            info["python_files"] = "Error counting"

        # 의존성 파일 존재 확인
        dep_files = ["pyproject.toml", "poetry.lock", "requirements.txt"]
        for dep_file in dep_files:
            path = self.project_root / dep_file
            info[f"has_{dep_file.replace('.', '_')}"] = path.exists()

        # Git 정보
        git_status = self.run_command("git status --porcelain", shell=True)
        info["git_clean"] = len(git_status or "") == 0

        git_branch = self.run_command("git branch --show-current")
        info["git_branch"] = git_branch or "Unknown"

        return info

    def get_environment_info(self) -> Dict[str, str]:
        """환경 변수 정보 (민감하지 않은 것만)"""
        safe_vars = ["PATH", "SHELL", "HOME", "USER", "LANG", "LC_ALL"]
        env_info = {}

        for var in safe_vars:
            value = os.environ.get(var)
            if value:
                # PATH는 너무 길어서 길이만 표시
                if var == "PATH":
                    env_info[var] = f"{len(value.split(':'))} paths"
                else:
                    env_info[var] = value

        return env_info

    def validate(self) -> Dict[str, Any]:
        """전체 검증 실행"""
        self.info = {
            "timestamp": self.run_command("date '+%Y-%m-%d %H:%M:%S'"),
            "python_versions": self.get_python_versions(),
            "system_info": self.get_system_info(),
            "project_info": self.get_project_info(),
            "environment_info": self.get_environment_info(),
            "validation_status": "completed",
        }

        return self.info

    def save_report(self, filename: str = "system_info_report.json") -> str:
        """검증 결과를 파일로 저장"""
        if not self.info:
            self.validate()

        report_path = self.project_root / filename
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.info, f, indent=2, ensure_ascii=False)

        return str(report_path)

    def print_report(self) -> None:
        """검증 결과 출력"""
        if not self.info:
            self.validate()

        print("🛡️ AFO Kingdom - System Information Validator")
        print("=" * 50)

        print("\n🐍 Python Versions:")
        for key, value in self.info["python_versions"].items():
            print(f"  {key}: {value}")

        print("\n💻 System Info:")
        for key, value in self.info["system_info"].items():
            print(f"  {key}: {value}")

        print("\n📁 Project Info:")
        for key, value in self.info["project_info"].items():
            print(f"  {key}: {value}")

        print("\n✅ Validation Status:", self.info["validation_status"])


def main() -> None:
    """메인 함수"""
    validator = SystemInfoValidator()

    # 검증 실행
    print("🔍 시스템 정보 검증 시작...")
    validator.validate()

    # 결과 출력
    validator.print_report()

    # 결과 저장
    report_file = validator.save_report()
    print(f"\n💾 검증 결과 저장됨: {report_file}")

    return validator.info


if __name__ == "__main__":
    main()
