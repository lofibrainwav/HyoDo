#!/usr/bin/env python3
"""
AFO 왕국 의존성 검증 시스템
Sequential Thinking: 단계별 의존성 검증 및 문제 해결

형님의 지적대로 더 견고한 검증 방식으로 개선:
1. 타임아웃 방지 메커니즘
2. 단계적 검증 방식
3. 상세한 에러 리포팅
4. 자동 복구 제안
"""

import asyncio
import sys
from pathlib import Path
from typing import Any


class DependencyVerifier:
    """
    견고한 의존성 검증 시스템
    Sequential Thinking 기반 단계별 검증
    """

    def __init__(self, project_root: Path, timeout_seconds: int = 10) -> None:
        self.project_root = project_root
        self.timeout_seconds = timeout_seconds
        self.results = {
            "core_packages": [],
            "dev_packages": [],
            "missing_packages": [],
            "version_conflicts": [],
            "import_errors": [],
            "success_count": 0,
            "total_tested": 0,
        }

    async def run_full_verification(self) -> dict[str, Any]:
        """
        전체 의존성 검증 실행 (Sequential Thinking Phase 1-3)
        """
        print("🏰 AFO 왕국 의존성 검증 시스템 시작")
        print("=" * 60)

        try:
            # Phase 1: 코어 패키지 검증 (빠른 우선순위)
            print("\n📦 Phase 1: 코어 패키지 검증 중...")
            await self._verify_core_packages()

            # Phase 2: 개발 패키지 검증 (선택적)
            print("\n🔧 Phase 2: 개발 패키지 검증 중...")
            await self._verify_dev_packages()

            # Phase 3: 누락 패키지 식별 및 제안
            print("\n🔍 Phase 3: 누락 패키지 분석 중...")
            await self._analyze_missing_packages()

            # Phase 4: 최종 보고서 생성
            print("\n📊 Phase 4: 최종 보고서 생성 중...")
            final_report = await self._generate_final_report()

            print("\n✅ 의존성 검증 시스템 완료!")
            return final_report

        except Exception as e:
            print(f"\n❌ 의존성 검증 시스템 실패: {e}")
            return {"error": str(e)}

    async def _verify_core_packages(self) -> None:
        """
        코어 패키지 검증 (Phase 1) - 가장 중요하고 가벼운 패키지들
        """
        core_packages = [
            ("redis", "redis"),
            ("fastapi", "fastapi"),
            ("uvicorn", "uvicorn"),
            ("pydantic", "pydantic"),
            ("google.genai", "google-genai"),
        ]

        for module_name, package_name in core_packages:
            result = await self._test_single_package(module_name, package_name, is_core=True)
            self.results["core_packages"].append(result)

    async def _verify_dev_packages(self) -> None:
        """
        개발 패키지 검증 (Phase 2) - 개발 시 필요한 패키지들
        """
        dev_packages = [
            ("black", "black"),
            ("isort", "isort"),
            ("ruff", "ruff"),
            ("pytest", "pytest"),
        ]

        for module_name, package_name in dev_packages:
            result = await self._test_single_package(module_name, package_name, is_core=False)
            self.results["dev_packages"].append(result)

    async def _test_single_package(
        self, module_name: str, package_name: str, is_core: bool = True
    ) -> dict[str, Any]:
        """
        단일 패키지 테스트 (타임아웃 방지)
        """
        self.results["total_tested"] += 1

        try:
            # 타임아웃으로 보호된 import 테스트
            result = await asyncio.wait_for(
                self._async_import_test(module_name), timeout=self.timeout_seconds
            )

            if result["success"]:
                version = result.get("version", "버전 확인 불가")
                print(f"  ✅ {package_name}: {version}")
                self.results["success_count"] += 1
                return {
                    "name": package_name,
                    "status": "success",
                    "version": version,
                    "is_core": is_core,
                }
            error_msg = result.get("error", "알 수 없는 오류")
            print(f"  ❌ {package_name}: {error_msg}")
            self.results["import_errors"].append(
                {
                    "package": package_name,
                    "error": error_msg,
                    "is_core": is_core,
                }
            )
            return {
                "name": package_name,
                "status": "error",
                "error": error_msg,
                "is_core": is_core,
            }

        except TimeoutError:
            print(f"  ⏰ {package_name}: 타임아웃 ({self.timeout_seconds}s)")
            self.results["import_errors"].append(
                {
                    "package": package_name,
                    "error": f"타임아웃 ({self.timeout_seconds}s)",
                    "is_core": is_core,
                }
            )
            return {
                "name": package_name,
                "status": "timeout",
                "error": f"타임아웃 ({self.timeout_seconds}s)",
                "is_core": is_core,
            }
        except Exception as e:
            error_msg = str(e)
            print(f"  ⚠️  {package_name}: 예외 발생 - {error_msg}")
            self.results["import_errors"].append(
                {
                    "package": package_name,
                    "error": error_msg,
                    "is_core": is_core,
                }
            )
            return {
                "name": package_name,
                "status": "exception",
                "error": error_msg,
                "is_core": is_core,
            }

    async def _async_import_test(self, module_name: str) -> dict[str, Any]:
        """
        비동기로 import 테스트 실행
        """

        def sync_import_test() -> None:
            try:
                module = __import__(module_name)
                version = getattr(module, "__version__", "버전 확인 불가")
                return {"success": True, "version": version}
            except ImportError as e:
                return {"success": False, "error": f"설치되지 않음 - {e}"}
            except Exception as e:
                return {"success": False, "error": f"기타 오류 - {e}"}

        # 별도 스레드에서 실행하여 메인 이벤트 루프 블록 방지
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_import_test)

    async def _analyze_missing_packages(self) -> None:
        """
        누락 패키지 분석 및 설치 제안 (Phase 3)
        """
        # pyproject.toml에서 선언된 의존성 확인
        pyproject_path = self.project_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                import tomllib

                with Path(pyproject_path).open("rb") as f:
                    pyproject_data = tomllib.load(f)

                # [tool.poetry.dependencies]에서 의존성 추출
                poetry_deps = (
                    pyproject_data.get("tool", {}).get("poetry", {}).get("dependencies", {})
                )
                # python 버전 선언 제외
                declared_deps = [dep_name for dep_name in poetry_deps if dep_name != "python"]

                # 실제 설치된 것과 비교
                for dep in declared_deps:
                    # 이미 테스트한 패키지는 건너뜀
                    tested_packages = [
                        p["name"]
                        for p in self.results["core_packages"] + self.results["dev_packages"]
                    ]
                    if dep not in tested_packages:
                        # 모듈 이름 변환 로직
                        module_name = self._convert_package_to_module_name(dep)
                        result = await self._test_single_package(module_name, dep, is_core=True)
                        if result["status"] != "success":
                            self.results["missing_packages"].append(result)

            except Exception as e:
                print(f"  ⚠️  pyproject.toml 분석 실패: {e}")

    async def _generate_final_report(self) -> dict[str, Any]:
        """
        최종 보고서 생성 (Phase 4)
        """
        # 통계 계산
        core_success = len([p for p in self.results["core_packages"] if p["status"] == "success"])
        core_total = len(self.results["core_packages"])

        dev_success = len([p for p in self.results["dev_packages"] if p["status"] == "success"])
        dev_total = len(self.results["dev_packages"])

        total_missing = len(self.results["missing_packages"])

        # 결과 출력
        print("\n📊 최종 의존성 검증 결과:")
        print(f"  • 코어 패키지: {core_success}/{core_total} 성공")
        print(f"  • 개발 패키지: {dev_success}/{dev_total} 성공")
        print(f"  • 누락 패키지: {total_missing}개")
        print(f"  • 총 테스트: {self.results['total_tested']}개")
        print(
            f"  • 성공률: {(self.results['success_count'] / self.results['total_tested'] * 100):.1f}%"
        )

        if self.results["import_errors"]:
            print("\n⚠️  import 오류가 있는 패키지들:")
            for error in self.results["import_errors"]:
                print(f"    - {error['package']}: {error['error']}")

        if self.results["missing_packages"]:
            print("\n💡 설치 제안:")
            missing_names = [p["name"] for p in self.results["missing_packages"]]
            print(f"    pip install {' '.join(missing_names)}")
            print("    # 또는")
            print(f"    poetry add {' '.join(missing_names)}")

        return {
            "summary": {
                "total_tested": self.results["total_tested"],
                "success_count": self.results["success_count"],
                "success_rate": (
                    self.results["success_count"] / self.results["total_tested"]
                    if self.results["total_tested"] > 0
                    else 0
                ),
                "core_packages": f"{core_success}/{core_total}",
                "dev_packages": f"{dev_success}/{dev_total}",
                "missing_packages": total_missing,
            },
            "details": {
                "core_packages": self.results["core_packages"],
                "dev_packages": self.results["dev_packages"],
                "missing_packages": self.results["missing_packages"],
                "import_errors": self.results["import_errors"],
            },
            "recommendations": self._generate_recommendations(),
        }

    def _convert_package_to_module_name(self, package_name: str) -> str:
        """
        패키지 이름을 실제 import할 모듈 이름으로 변환
        """
        # 특수 케이스들 처리
        conversion_map = {
            "python-frontmatter": "frontmatter",
            "kafka-python": "kafka",
            "sentence-transformers": "sentence_transformers",
            "scikit-learn": "sklearn",
            "python-dotenv": "dotenv",
            "beautifulsoup4": "bs4",
            "python-multipart": "multipart",
            "python-jose": "jose",
            "python-dateutil": "dateutil",
            "python-magic": "magic",
            "gitpython": "git",
            "pyyaml": "yaml",
            "ruamel.yaml": "ruamel.yaml",
            "psycopg2-binary": "psycopg2",
            "pymongo": "pymongo",
            "qdrant-client": "qdrant_client",
            "chromadb": "chromadb",
            "eth-account": "eth_account",
            "web3": "web3",
            "neo4j": "neo4j",
            "sunoai": "sunoai",
            "docker": "docker",
            "markdown": "markdown",
            "pgvector": "pgvector",
            "ragas": "ragas",
            "boto3": "boto3",
            "google-genai": "google.genai",
        }

        # 변환 맵에 있는 경우 변환
        if package_name in conversion_map:
            return conversion_map[package_name]

        # 일반적인 경우: 하이픈을 언더스코어로 변환
        return package_name.replace("-", "_")

    def _generate_recommendations(self) -> list[str]:
        """
        개선 권장사항 생성
        """
        recommendations = []

        if self.results["import_errors"]:
            recommendations.append("import 오류가 있는 패키지들을 우선 설치하거나 재설치")

        if self.results["missing_packages"]:
            recommendations.append("pyproject.toml에 선언된 누락 패키지들을 설치")

        recommendations.extend(
            [
                "Poetry 대신 pip을 사용하여 더 빠른 의존성 관리 고려",
                "가상환경을 재생성하여 깨끗한 상태에서 시작",
                "requirements.txt 파일을 생성하여 명시적 의존성 관리",
            ]
        )

        return recommendations


async def main():
    """
    메인 함수
    """
    project_root = Path(__file__).parent.parent

    # 타임아웃을 더 짧게 설정하여 빠른 실패 유도
    verifier = DependencyVerifier(project_root, timeout_seconds=5)

    results = await verifier.run_full_verification()

    if "error" in results:
        print(f"\n❌ 검증 실패: {results['error']}")
        sys.exit(1)
    else:
        summary = results.get("summary", {})
        success_rate = summary.get("success_rate", 0) * 100

        if success_rate >= 80:
            print(f"\n✅ 의존성 상태 양호 (성공률: {success_rate:.1f}%)")
        elif success_rate >= 60:
            print(f"\n⚠️  의존성 상태 보통 (성공률: {success_rate:.1f}%)")
        else:
            print(f"\n❌ 의존성 상태 불량 (성공률: {success_rate:.1f}%) - 즉시 조치 필요")


if __name__ == "__main__":
    asyncio.run(main())
