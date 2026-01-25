"""
모듈 로딩 책임 모듈 (SOLID: 단일 책임 원칙)

이 모듈은 코드 검증 시스템의 모듈 로딩 기능을 담당합니다.
- code_review_node.py 파일 탐색 및 로딩
- 모듈 검증 및 안전한 임포트
"""

import importlib.util
from pathlib import Path


def load_review_module(root: Path = Path(".")) -> tuple:
    """
    code_review_node 모듈을 안전하게 로딩합니다.

    Args:
        root: 검색 시작 디렉토리

    Returns:
        tuple: (loaded_module, module_path)

    Raises:
        FileNotFoundError: code_review_node.py를 찾을 수 없는 경우
        ImportError: 모듈 로딩 실패 시
    """
    # code_review_node.py 파일 탐색
    hits = list(root.rglob("code_review_node.py"))
    if not hits:
        raise FileNotFoundError("code_review_node.py not found in project")

    target = hits[0]
    print(f"Found code_review_node.py at: {target}")

    # 모듈 스펙 생성 및 검증
    spec = importlib.util.spec_from_file_location("code_review_node", str(target))
    if spec is None:
        raise ImportError(f"Could not create module spec for {target}")

    # 모듈 로딩
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        return mod, target
    except Exception as e:
        raise ImportError(f"Failed to load module {target}: {e}")
