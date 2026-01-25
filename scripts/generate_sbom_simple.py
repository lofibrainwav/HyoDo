#!/usr/bin/env python3
"""
Phase 4: SBOM (Software Bill of Materials) 생성 스크립트 (간단 버전)
眞善美孝永 5기둥 철학에 의거한 의존성 투명성 확보

이 스크립트는 AFO 왕국의 모든 의존성을 SBOM 형식으로 생성합니다.
requirements.txt 기반 간단한 JSON SBOM 생성
"""

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/Users/brnestrm/AFO_Kingdom/.cursor/debug.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

try:
    import pkg_resources

    PKG_RESOURCES_AVAILABLE = True
except ImportError:
    PKG_RESOURCES_AVAILABLE = False


def parse_requirements(requirements_path: Path) -> list[dict[str, Any]]:
    """requirements.txt 파싱"""
    logger.info("[眞] requirements.txt 파싱 시작: %s", requirements_path)
    components = []

    if not requirements_path.exists():
        logger.warning("[眞] 파일 없음: %s", requirements_path)
        return components

    logger.info("[眞] 파일 읽기 시작: %s", requirements_path)
    with Path(requirements_path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # 버전 정보 추출
            if "==" in line:
                name, version = line.split("==", 1)
                name = name.strip()
                version = version.strip()
            elif ">=" in line:
                name, version = line.split(">=", 1)
                name = name.strip()
                version = f">={version.strip()}"
            elif "~=" in line:
                name, version = line.split("~=", 1)
                name = name.strip()
                version = f"~={version.strip()}"
            else:
                name = line
                version = None

            components.append(
                {
                    "type": "library",
                    "name": name,
                    "version": version or "unknown",
                }
            )
            logger.debug(f"[眞] 패키지 추가: {name} {version or 'unknown'}")

    logger.info(f"[眞] 파싱 완료: {len(components)}개 패키지 발견")
    return components


def generate_sbom_json(components: list[dict[str, Any]], output_path: Path) -> None:
    """CycloneDX 형식의 간단한 JSON SBOM 생성"""
    logger.info(f"[永] SBOM 생성 시작: {output_path} ({len(components)}개 컴포넌트)")
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(UTC).isoformat(),
            "tools": [
                {
                    "vendor": "AFO Kingdom",
                    "name": "SBOM Generator",
                    "version": "1.0.0",
                }
            ],
            "component": {
                "type": "application",
                "name": "AFO Kingdom",
                "version": "1.0.0",
            },
        },
        "components": components,
    }

    logger.info("[永] JSON 파일 쓰기 시작: %s", output_path)
    with Path(output_path).open("w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2, ensure_ascii=False)

    logger.info("[永] SBOM 생성 완료: %s", output_path)
    print(f"✅ SBOM generated: {output_path}")


def get_installed_packages() -> list[dict[str, Any]]:
    """현재 설치된 패키지 목록 가져오기"""
    logger.info("[眞] 설치된 패키지 목록 수집 시작")
    if not PKG_RESOURCES_AVAILABLE:
        logger.warning("[眞] pkg_resources 사용 불가")
        return []

    logger.info("[眞] working_set 순회 시작")
    components = [
        {
            "type": "library",
            "name": dist.project_name,
            "version": dist.version,
        }
        for dist in pkg_resources.working_set
    ]

    logger.info(f"[眞] 설치된 패키지 수집 완료: {len(components)}개")
    return components


def main() -> int:
    """메인 함수"""
    logger.info("=" * 80)
    logger.info("🏰 AFO Kingdom - SBOM (Software Bill of Materials) 생성")
    logger.info("=" * 80)
    print("=" * 80)
    print("🏰 AFO Kingdom - SBOM (Software Bill of Materials) 생성")
    print("=" * 80)
    print()

    # 출력 디렉토리 생성
    output_dir = Path("sbom")
    logger.info("[孝] 출력 디렉토리 생성: %s", output_dir)
    output_dir.mkdir(exist_ok=True)

    # 1. requirements.txt 파일들에서 SBOM 생성
    requirements_files = [
        ("packages/afo-core/requirements.txt", "afo_core"),
        ("packages/trinity-os/requirements.txt", "trinity_os"),
        ("packages/afo-core/requirements_minimal.txt", "afo_core_minimal"),
    ]

    all_components = []
    success_count = 0

    for req_path_str, name in requirements_files:
        req_path = Path(req_path_str)
        logger.info("[眞] requirements 파일 확인: %s", req_path)
        if req_path.exists():
            components = parse_requirements(req_path)
            if components:
                output_path = output_dir / f"{name}_sbom.json"
                logger.info("[永] SBOM 생성 시작: %s", name)
                generate_sbom_json(components, output_path)
                all_components.extend(components)
                success_count += 1
                logger.info("[永] SBOM 생성 성공: %s", name)
            else:
                logger.warning("[眞] 컴포넌트 없음: %s", name)
        else:
            logger.warning("[眞] 파일 없음: %s", req_path)

    # 2. 현재 환경에서 SBOM 생성 (종합)
    logger.info("[眞] 환경 패키지 수집 시작")
    if PKG_RESOURCES_AVAILABLE:
        env_components = get_installed_packages()
        if env_components:
            env_output = output_dir / "environment_sbom.json"
            logger.info(f"[永] 환경 SBOM 생성 시작: {len(env_components)}개 패키지")
            generate_sbom_json(env_components, env_output)
            success_count += 1
            logger.info("[永] 환경 SBOM 생성 성공")
        else:
            logger.warning("[眞] 환경 패키지 없음")
    else:
        logger.warning("[眞] pkg_resources 사용 불가 - 환경 SBOM 스킵")

    # 3. 통합 SBOM 생성
    logger.info(f"[永] 통합 SBOM 생성 시작: {len(all_components)}개 컴포넌트")
    if all_components:
        # 중복 제거
        unique_components = {}
        for comp in all_components:
            key = (comp["name"], comp.get("version"))
            if key not in unique_components:
                unique_components[key] = comp

        logger.info(f"[永] 중복 제거 완료: {len(unique_components)}개 고유 컴포넌트")
        combined_output = output_dir / "combined_sbom.json"
        generate_sbom_json(list(unique_components.values()), combined_output)
        success_count += 1
        logger.info("[永] 통합 SBOM 생성 성공")
    else:
        logger.warning("[眞] 통합할 컴포넌트 없음")

    logger.info("=" * 80)
    print()
    print("=" * 80)
    if success_count > 0:
        logger.info("[永] SBOM 생성 완료: %s개 파일", success_count)
        logger.info(f"[永] 출력 디렉토리: {output_dir.absolute()}")
        print(f"✅ SBOM 생성 완료: {success_count}개 파일")
        print(f"   출력 디렉토리: {output_dir.absolute()}")
    else:
        logger.error("[眞] SBOM 생성 실패")
        print("❌ SBOM 생성 실패")
        return 1

    logger.info("=" * 80)
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
