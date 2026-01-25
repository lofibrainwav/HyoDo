#!/usr/bin/env python3
"""
Phase 4: SBOM (Software Bill of Materials) 생성 스크립트
眞善美孝永 5기둥 철학에 의거한 의존성 투명성 확보

이 스크립트는 cyclonedx-py CLI를 사용하여 SBOM을 생성합니다.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: list[str]) -> bool:
    """명령어 실행 및 결과 반환"""
    try:
        subprocess.run(command, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command {' '.join(command)}: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"⚠️  Command not found: {command[0]}")
        print("   Install with: pip install cyclonedx-bom")
        return False


def main() -> int:
    print("=" * 80)
    print("🏰 AFO Kingdom - SBOM (Software Bill of Materials) 생성 (CLI Mode)")
    print("=" * 80)
    print()

    # 출력 디렉토리 생성
    output_dir = Path("artifacts/sbom")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1.requirements.txt 파일들에서 SBOM 생성
    requirements_files = [
        Path("packages/afo-core/requirements.txt"),
        Path("packages/trinity-os/requirements.txt"),
    ]

    success_count = 0
    for req_file in requirements_files:
        if req_file.exists():
            output_base = output_dir / f"{req_file.parts[-2]}_{req_file.stem}_sbom"

            # JSON format
            if run_command(
                [
                    "cyclonedx-py",
                    "requirements",
                    str(req_file),
                    "--output-format",
                    "JSON",
                    "--output-file",
                    str(output_base.with_suffix(".json")),
                ]
            ):
                print(f"✅ SBOM (JSON) generated: {output_base.with_suffix('.json')}")

            # XML format
            if run_command(
                [
                    "cyclonedx-py",
                    "requirements",
                    str(req_file),
                    "--output-format",
                    "XML",
                    "--output-file",
                    str(output_base.with_suffix(".xml")),
                ]
            ):
                print(f"✅ SBOM (XML) generated: {output_base.with_suffix('.xml')}")
                success_count += 1

    # 2. 현재 환경에서 SBOM 생성
    env_output = output_dir / "environment_sbom"
    if run_command(
        [
            "cyclonedx-py",
            "environment",
            "--output-format",
            "JSON",
            "--output-file",
            str(env_output.with_suffix(".json")),
        ]
    ):
        print(f"✅ Environment SBOM (JSON) generated: {env_output.with_suffix('.json')}")
        success_count += 1

    print()
    print("=" * 80)
    if success_count > 0:
        print(f"✅ SBOM 생성 완료: {success_count}개 세트")
        print(f"   출력 디렉토리: {output_dir.absolute()}")
        return 0
    print("❌ SBOM 생성 실패")
    return 1


if __name__ == "__main__":
    sys.exit(main())
