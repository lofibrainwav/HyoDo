#!/usr/bin/env python3
"""
AFO 왕국 SBOM 생성 스크립트 - 수정된 버전
CycloneDX CLI 도구를 사용한 올바른 SBOM 생성

원래 스크립트의 문제점:
- cyclonedx_py.parser import 시도 (존재하지 않는 모듈)
- 실제로는 cyclonedx-bom CLI 도구를 사용해야 함

수정된 방식:
- subprocess로 CLI 도구 직접 호출
- 환경 변수 및 requirements.txt 처리
- 에러 핸들링 강화
"""

import json
import subprocess
import sys
from pathlib import Path


def run_cyclonedx_command(command: list[str], output_file: str | None = None) -> bool:
    """
    CycloneDX CLI 명령어 실행

    Args:
        command: 실행할 명령어 리스트
        output_file: 출력 파일 경로 (있으면 성공 확인)

    Returns:
        성공 여부
    """
    try:
        print(f"실행 명령어: {' '.join(command)}")

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,  # 5분 타임아웃
        )

        if result.returncode == 0:
            print("✅ CycloneDX 명령어 실행 성공")

            # 출력 파일 확인
            if output_file and Path(output_file).exists():
                file_size = Path(output_file).stat().st_size
                print(f"✅ 출력 파일 생성됨: {output_file} ({file_size} bytes)")

                # JSON 유효성 검증
                if output_file.endswith(".json"):
                    try:
                        with Path(output_file).open(encoding="utf-8") as f:
                            data = json.load(f)
                        components_count = len(data.get("components", []))
                        print(f"✅ JSON 유효성 검증 통과: {components_count}개 컴포넌트")
                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON 유효성 검증 실패: {e}")
                        return False

            return True
        print(f"❌ CycloneDX 명령어 실패 (코드: {result.returncode})")
        if result.stderr:
            print(f"stderr: {result.stderr[:500]}...")
        if result.stdout:
            print(f"stdout: {result.stdout[:500]}...")
        return False

    except subprocess.TimeoutExpired:
        print("❌ CycloneDX 명령어 타임아웃 (5분 초과)")
        return False
    except Exception as e:
        print(f"❌ CycloneDX 명령어 실행 중 예외: {e}")
        return False


def generate_sbom_from_environment(output_path: Path) -> bool:
    """
    현재 Python 환경에서 SBOM 생성 (CLI 방식)
    """
    print(f"📦 환경 기반 SBOM 생성 시작: {output_path}")

    # CycloneDX CLI 명령어 구성
    command = ["cyclonedx-py", "environment", "--output-file", str(output_path)]

    return run_cyclonedx_command(command, str(output_path))


def generate_sbom_from_requirements(requirements_path: Path, output_path: Path) -> bool:
    """
    requirements.txt에서 SBOM 생성 (CLI 방식)
    """
    if not requirements_path.exists():
        print(f"⚠️  requirements 파일이 존재하지 않음: {requirements_path}")
        return False

    print(f"📋 requirements 기반 SBOM 생성 시작: {requirements_path} -> {output_path}")

    # CycloneDX CLI 명령어 구성
    command = [
        "cyclonedx-py",
        "requirements",
        str(requirements_path),
        "--output-file",
        str(output_path),
    ]

    return run_cyclonedx_command(command, str(output_path))


def check_cyclonedx_availability() -> bool:
    """
    CycloneDX CLI 도구 사용 가능 여부 확인
    """
    try:
        result = subprocess.run(
            ["cyclonedx-py", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


def main() -> int:
    """메인 함수"""
    print("=" * 80)
    print("🏰 AFO 왕국 - CycloneDX SBOM 생성 (CLI 방식)")
    print("=" * 80)
    print()

    # CycloneDX CLI 도구 확인
    if not check_cyclonedx_availability():
        print("❌ cyclonedx-bom이 설치되지 않았습니다.")
        print()
        print("설치 방법:")
        print("  pip install cyclonedx-bom")
        print("  또는")
        print("  poetry add cyclonedx-bom --group dev")
        print()
        print("설치 후 다시 실행해주세요.")
        return 1

    print("✅ CycloneDX CLI 도구 확인 완료")
    print()

    # 출력 디렉토리 생성
    output_dir = Path("sbom")
    output_dir.mkdir(exist_ok=True)

    success_count = 0
    total_attempts = 0

    # 1. requirements.txt 파일들에서 SBOM 생성
    requirements_files = [
        Path("packages/afo-core/requirements.txt"),
        Path("packages/trinity-os/requirements.txt"),
        Path("packages/afo-core/requirements_minimal.txt"),
    ]

    print("📋 Requirements 기반 SBOM 생성:")
    for req_file in requirements_files:
        total_attempts += 1
        if req_file.exists():
            output_path = output_dir / f"{req_file.stem}_sbom.json"
            if generate_sbom_from_requirements(req_file, output_path):
                success_count += 1
        else:
            print(f"  ⚠️  {req_file} 파일이 존재하지 않음 (건너뜀)")

    print()

    # 2. 현재 환경에서 SBOM 생성 (종합)
    print("🌍 환경 기반 SBOM 생성:")
    total_attempts += 1
    env_output = output_dir / "environment_sbom.json"
    if generate_sbom_from_environment(env_output):
        success_count += 1

    print()
    print("=" * 80)

    if success_count > 0:
        print(f"✅ SBOM 생성 완료: {success_count}/{total_attempts} 성공")

        # 생성된 파일들 목록
        sbom_files = list(output_dir.glob("*.json"))
        if sbom_files:
            print(f"📁 생성된 SBOM 파일들 ({len(sbom_files)}개):")
            for sbom_file in sorted(sbom_files):
                size = sbom_file.stat().st_size
                print(f"   • {sbom_file.name} ({size} bytes)")

        print("\n💡 다음 단계:")
        print("   python scripts/sbom_to_skills.py sbom/environment_sbom.json")
        print("   # Skills Registry 생성")
    else:
        print("❌ SBOM 생성 실패")
        print("\n💡 문제 해결:")
        print("   1. cyclonedx-bom 버전 확인: pip show cyclonedx-bom")
        print("   2. Python 환경 재설치: pip install --force-reinstall cyclonedx-bom")
        return 1

    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
