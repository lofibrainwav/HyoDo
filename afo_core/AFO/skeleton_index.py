"""
골격 인덱서: AFO 왕국 4폴더 구조를 스캔하여 기존 구현을 인덱싱
MD→티켓 변환 시 기존 코드 재사용을 위한 기반 데이터 생성
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModuleInfo:
    """모듈 정보"""

    path: str
    name: str
    type: str  # 'package', 'module', 'service', 'config'
    dependencies: list[str]
    description: str = ""


@dataclass
class SkeletonIndex:
    """골격 인덱스"""

    packages: dict[str, list[ModuleInfo]]
    services: dict[str, list[ModuleInfo]]
    configs: dict[str, list[ModuleInfo]]
    docs: dict[str, list[str]]
    last_updated: str


class SkeletonIndexer:
    """
    AFO 왕국 골격 인덱서
    4폴더 (afo/, afo_kingdom/, trinity-os/, sixxon/) 구조를 스캔
    """

    def __init__(self, root_path=None) -> None:
        if root_path is None:
            # This file is at packages/afo-core/AFO/skeleton_index.py
            # So repo root is 3 parents up
            root_path = str(Path(__file__).resolve().parents[3])
        self.root_path = Path(root_path)
        self.target_folders = [
            "packages/afo-core",  # afo/
            "packages/dashboard",  # afo_kingdom/
            "packages/trinity-os",  # trinity-os/
            "packages/sixxon",  # sixxon/ (존재하지 않을 수 있음)
        ]

    def scan_folders(self) -> SkeletonIndex:
        """4폴더 구조 스캔하여 인덱스 생성"""
        packages = {}
        services = {}
        configs = {}
        docs = {}

        for folder in self.target_folders:
            folder_path = self.root_path / folder
            if not folder_path.exists():
                continue

            folder_name = folder.split("/")[-1]

            # 패키지 스캔
            packages[folder_name] = self._scan_packages(folder_path)

            # 서비스 스캔
            services[folder_name] = self._scan_services(folder_path)

            # 설정 파일 스캔
            configs[folder_name] = self._scan_configs(folder_path)

            # 문서 스캔
            docs[folder_name] = self._scan_docs(folder_path)

        return SkeletonIndex(
            packages=packages,
            services=services,
            configs=configs,
            docs=docs,
            last_updated=self._get_timestamp(),
        )

    def _scan_packages(self, folder_path: Path) -> list[ModuleInfo]:
        """Python 패키지 구조 스캔"""
        modules = []

        # __init__.py 파일 찾기
        for init_file in folder_path.rglob("__init__.py"):
            if str(init_file).count("/site-packages/") > 0:
                continue  # 시스템 패키지 제외

            module_path = init_file.parent
            module_name = module_path.name

            # 모듈 타입 판별
            module_type = self._classify_module(module_path)

            # 의존성 분석
            dependencies = self._analyze_dependencies(module_path)

            modules.append(
                ModuleInfo(
                    path=str(module_path.relative_to(self.root_path)),
                    name=module_name,
                    type=module_type,
                    dependencies=dependencies,
                    description=self._extract_description(module_path),
                )
            )

        return modules

    def _scan_services(self, folder_path: Path) -> list[ModuleInfo]:
        """서비스 구조 스캔"""
        services = []

        # 서비스 관련 파일 찾기
        service_patterns = ["**/services/**", "**/*service*.py", "**/*client*.py"]

        for pattern in service_patterns:
            for service_file in folder_path.glob(pattern):
                if service_file.is_file() and service_file.suffix == ".py":
                    service_name = service_file.stem

                    services.append(
                        ModuleInfo(
                            path=str(service_file.relative_to(self.root_path)),
                            name=service_name,
                            type="service",
                            dependencies=self._analyze_file_dependencies(service_file),
                            description=f"Service module: {service_name}",
                        )
                    )

        return services

    def _scan_configs(self, folder_path: Path) -> list[ModuleInfo]:
        """설정 파일 스캔"""
        configs = []

        config_patterns = ["**/*.yaml", "**/*.yml", "**/*.json", "**/*.toml", "**/*.py"]

        for pattern in config_patterns:
            for config_file in folder_path.glob(pattern):
                if "config" in str(config_file).lower() or "settings" in str(config_file).lower():
                    config_name = config_file.stem

                    configs.append(
                        ModuleInfo(
                            path=str(config_file.relative_to(self.root_path)),
                            name=config_name,
                            type="config",
                            dependencies=[],
                            description=f"Configuration file: {config_name}",
                        )
                    )

        return configs

    def _scan_docs(self, folder_path: Path) -> list[str]:
        """문서 파일 스캔"""
        docs = []

        for md_file in folder_path.glob("**/*.md"):
            docs.append(str(md_file.relative_to(self.root_path)))

        return docs

    def _classify_module(self, module_path: Path) -> str:
        """모듈 타입 분류"""
        path_str = str(module_path)

        if "api" in path_str:
            return "api"
        elif "services" in path_str:
            return "service"
        elif "models" in path_str or "schemas" in path_str:
            return "model"
        elif "utils" in path_str or "helpers" in path_str:
            return "utility"
        elif "tests" in path_str:
            return "test"
        else:
            return "package"

    def _analyze_dependencies(self, module_path: Path) -> list[str]:
        """모듈 의존성 분석"""
        dependencies = []

        for py_file in module_path.glob("**/*.py"):
            deps = self._analyze_file_dependencies(py_file)
            dependencies.extend(deps)

        return list(set(dependencies))  # 중복 제거

    def _analyze_file_dependencies(self, file_path: Path) -> list[str]:
        """단일 파일 의존성 분석"""
        dependencies = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

                # import 문 분석
                lines = content.split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith("from ") or line.startswith("import "):
                        # 간단한 의존성 추출 (개선 가능)
                        if "from afo" in line or "from AFO" in line:
                            dependencies.append("internal")
                        elif "from packages" in line:
                            dependencies.append("package")

        except Exception:
            pass

        return dependencies

    def _extract_description(self, module_path: Path) -> str:
        """모듈 설명 추출"""
        # __init__.py 또는 README에서 설명 추출 (간단 구현)
        init_file = module_path / "__init__.py"
        if init_file.exists():
            try:
                with open(init_file, encoding="utf-8") as f:
                    content = f.read()
                    # docstring 추출 시도
                    lines = content.split("\n")
                    in_docstring = False
                    docstring_lines = []

                    for line in lines[:20]:  # 처음 20줄만 확인
                        if '"""' in line or "'''" in line:
                            if in_docstring:
                                break
                            in_docstring = True
                        elif in_docstring:
                            docstring_lines.append(line.strip())

                    if docstring_lines:
                        return " ".join(docstring_lines[:3])  # 처음 3줄

            except Exception:
                pass

        return f"Module: {module_path.name}"

    def _get_timestamp(self) -> str:
        """현재 타임스탬프"""
        from datetime import datetime

        return datetime.now().isoformat()

    def save_index(self, index: SkeletonIndex, output_path: str = "skeleton_index.json") -> None:
        """인덱스를 JSON 파일로 저장"""
        data = {
            "packages": {k: [vars(m) for m in v] for k, v in index.packages.items()},
            "services": {k: [vars(m) for m in v] for k, v in index.services.items()},
            "configs": {k: [vars(m) for m in v] for k, v in index.configs.items()},
            "docs": index.docs,
            "last_updated": index.last_updated,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_index(self, input_path: str = "skeleton_index.json") -> SkeletonIndex:
        """JSON 파일에서 인덱스 로드"""
        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)

        packages = {}
        for k, v in data["packages"].items():
            packages[k] = [ModuleInfo(**m) for m in v]

        services = {}
        for k, v in data["services"].items():
            services[k] = [ModuleInfo(**m) for m in v]

        configs = {}
        for k, v in data["configs"].items():
            configs[k] = [ModuleInfo(**m) for m in v]

        return SkeletonIndex(
            packages=packages,
            services=services,
            configs=configs,
            docs=data["docs"],
            last_updated=data["last_updated"],
        )


def main() -> None:
    """CLI 인터페이스"""
    indexer = SkeletonIndexer()
    index = indexer.scan_folders()

    print(f"골격 인덱스 생성 완료: {len(index.packages)}개 폴더, {index.last_updated}")
    indexer.save_index(index)

    print("인덱스 저장됨: skeleton_index.json")


if __name__ == "__main__":
    main()
