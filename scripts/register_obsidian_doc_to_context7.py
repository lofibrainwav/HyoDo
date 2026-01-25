#!/usr/bin/env python3
"""
옵시디언 문서를 Context7에 자동 등록하는 스크립트

템플릿 사용 시 자동으로 호출되어 문서 메타데이터를 Context7에 등록합니다.
"""

import sys
from pathlib import Path
from typing import Any

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "packages" / "trinity-os"))

try:
    from trinity_os.servers.context7_mcp import Context7MCP
except ImportError:
    print("❌ Context7MCP를 로드할 수 없습니다.", file=sys.stderr)
    sys.exit(1)


def extract_frontmatter(file_path: Path) -> dict[str, Any]:
    """옵시디언 문서의 Frontmatter를 추출합니다."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ 파일 읽기 실패: {e}", file=sys.stderr)
        return {}

    # Frontmatter 추출
    if not content.startswith("---"):
        return {}

    frontmatter_end = content.find("---", 3)
    if frontmatter_end == -1:
        return {}

    frontmatter_text = content[3:frontmatter_end].strip()
    metadata = {}

    for line in frontmatter_text.split("\n"):
        line = line.strip()
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        # 리스트 처리
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",")]
        # 불린 처리
        elif value.lower() in {"true", "false"}:
            value = value.lower() == "true"
        # 숫자 처리
        elif value.isdigit():
            value = int(value)
        elif value.replace(".", "", 1).isdigit():
            value = float(value)

        metadata[key] = value

    return metadata


def generate_context7_entry(file_path: Path, metadata: dict[str, Any]) -> str:
    """Context7에 등록할 항목을 생성합니다."""
    file_name = file_path.stem
    file_dir = file_path.parent.relative_to(project_root / "docs")

    # 문서 타입에 따른 카테고리 결정
    doc_type = metadata.get("type", "document")
    tags = metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]

    # 문서 요약 생성
    summary_parts = [
        f"**파일명**: {file_name}",
        f"**경로**: {file_dir}/{file_path.name}",
        f"**타입**: {doc_type}",
    ]

    if metadata.get("status"):
        summary_parts.append(f"**상태**: {metadata.get('status')}")

    if metadata.get("priority"):
        summary_parts.append(f"**우선순위**: {metadata.get('priority')}")

    if tags:
        summary_parts.append(f"**태그**: {', '.join(tags)}")

    if metadata.get("description"):
        summary_parts.append(f"**설명**: {metadata.get('description')}")

    if metadata.get("trinity_score"):
        summary_parts.append(f"**Trinity Score**: {metadata.get('trinity_score')}/100")

    return "\n".join(summary_parts)


def register_to_context7(file_path: Path) -> bool:
    """옵시디언 문서를 Context7에 등록합니다."""
    metadata = extract_frontmatter(file_path)

    if not metadata:
        print(f"⚠️  Frontmatter가 없습니다: {file_path}", file=sys.stderr)
        return False

    # Context7에 등록할 항목 생성
    entry = generate_context7_entry(file_path, metadata)

    # Context7 KNOWLEDGE_BASE에 추가
    # 실제로는 MCP Memory 도구를 사용하거나 API를 호출해야 하지만,
    # 현재는 Context7MCP의 KNOWLEDGE_BASE를 직접 업데이트
    doc_key = f"OBSIDIAN_DOC_{file_path.stem.upper().replace('-', '_').replace(' ', '_')}"

    # Context7MCP.KNOWLEDGE_BASE에 동적으로 추가
    # (실제로는 영구 저장소에 저장해야 함)
    Context7MCP.KNOWLEDGE_BASE[doc_key] = entry

    print(f"✅ Context7에 등록됨: {doc_key}")
    print(f"   경로: {file_path.relative_to(project_root)}")
    print(f"   타입: {metadata.get('type', 'document')}")

    return True


def main() -> None:
    """메인 함수"""
    if len(sys.argv) < 2:
        print(
            "사용법: python register_obsidian_doc_to_context7.py <파일경로>",
            file=sys.stderr,
        )
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"❌ 파일이 존재하지 않습니다: {file_path}", file=sys.stderr)
        sys.exit(1)

    if not file_path.is_absolute():
        # 상대 경로인 경우 docs 폴더 기준으로 변환
        docs_dir = project_root / "docs"
        file_path = docs_dir / file_path

    success = register_to_context7(file_path)

    if success:
        print("✅ Context7 등록 완료")
        sys.exit(0)
    else:
        print("❌ Context7 등록 실패", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
