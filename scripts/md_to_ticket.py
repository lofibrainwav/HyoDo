#!/usr/bin/env python3
"""
MD→티켓 자동 변환 CLI
형님이 작성한 MD 파일을 파싱하여 티켓으로 자동 변환
"""

import os
import subprocess
import sys
from pathlib import Path

# 프로젝트 루트
project_root = Path(__file__).parent.parent


def main() -> None:
    """메인 CLI 함수"""
    if len(sys.argv) < 2:
        print("사용법: python md_to_ticket.py <md_file> [priority] [complexity]")
        print("예시: python md_to_ticket.py docs/new_feature.md high 7")
        print("\n옵션:")
        print("  priority: high, medium, low (기본값: medium)")
        print("  complexity: 1-10 (기본값: 5)")
        return 1

    md_file = sys.argv[1]
    priority = sys.argv[2] if len(sys.argv) > 2 else "medium"
    complexity = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    # 파일 존재 확인
    if not os.path.exists(md_file):
        print(f"❌ 파일을 찾을 수 없습니다: {md_file}")
        return 1

    # 유효성 검증
    if priority not in ["high", "medium", "low"]:
        print(f"❌ 잘못된 우선순위: {priority}. high, medium, low 중 하나여야 합니다.")
        return 1

    if not 1 <= complexity <= 10:
        print(f"❌ 잘못된 복잡도: {complexity}. 1-10 범위여야 합니다.")
        return 1

    try:
        print(f"🔄 MD 파일 파싱 중: {md_file}")

        # 1. MD 파일 읽기
        content = Path(md_file).read_text(encoding="utf-8")

        # 2. MD 파싱 (subprocess로 실행)
        print("🔄 MD 파싱 중...")
        parse_result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"""
import sys
sys.path.insert(0, 'packages/afo-core')
from afo.md_parser import MDParser
import json

content = '''{content.replace("'", "\\'")}'''
parser = MDParser()
parsed = parser.parse_md(content)
print(json.dumps({{
    'goal': parsed.goal,
    'files_to_create': parsed.files_to_create,
    'files_to_update': parsed.files_to_update,
    'raw_notes': parsed.raw_notes,
    'constraints': parsed.constraints
}}))
""",
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        if parse_result.returncode != 0:
            print(f"❌ MD 파싱 실패: {parse_result.stderr}")
            return 1

        import json

        parsed_data = json.loads(parse_result.stdout.strip())
        print("✅ MD 파싱 완료")

        # 3. 골격 인덱스 생성 (이미 생성되어 있음)
        print("🔄 골격 인덱스 확인 중...")
        index_file = project_root / "skeleton_index.json"
        if not index_file.exists():
            print("🔄 골격 인덱스 생성 중...")
            index_result = subprocess.run(
                [sys.executable, "packages/afo-core/afo/skeleton_index.py"],
                check=False,
                cwd=project_root,
            )
            if index_result.returncode != 0:
                print("❌ 골격 인덱스 생성 실패")
                return 1

        print("✅ 골격 인덱스 준비됨")

        # 4. 매칭 및 티켓 생성을 하나의 스크립트로 실행
        print("🔄 매칭 및 티켓 생성 중...")
        match_script = f"""
import sys
import json
sys.path.insert(0, 'packages/afo-core')
from afo.md_parser import MDParser
from afo.matching_engine import MatchingEngine
from afo.ticket_generator import TicketGenerator
from afo.skeleton_index import SkeletonIndexer

# 데이터 복원
parsed_data = {json.dumps(parsed_data)}

# 객체 재생성
class ParsedMD:
    def __init__(self, data):
        self.goal = data['goal']
        self.files_to_create = data.get('files_to_create', [])
        self.files_to_update = data.get('files_to_update', [])
        self.raw_notes = data['raw_notes']
        self.constraints = data.get('constraints', [])

parsed_md = ParsedMD(parsed_data)

# 골격 인덱스 로드
indexer = SkeletonIndexer()
skeleton_index = indexer.load_index()

# 매칭 실행
engine = MatchingEngine(skeleton_index)
matching_result = engine.find_candidates(parsed_md)

# 티켓 생성
generator = TicketGenerator()
ticket_id = generator.generate_ticket(
    parsed_md, matching_result,
    priority='{priority}', complexity={complexity}
)

print(f"TICKET_ID:{{ticket_id}}")
print(f"CANDIDATES:{{len(matching_result.candidates)}}")
if matching_result.best_match:
    print(f"BEST_MATCH:{{matching_result.best_match.module.path}}")
    print(f"SIMILARITY:{{matching_result.best_match.similarity_score:.2f}}")
"""

        match_result = subprocess.run(
            [sys.executable, "-c", match_script],
            check=False,
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        if match_result.returncode != 0:
            print(f"❌ 매칭/티켓 생성 실패: {match_result.stderr}")
            return 1

        # 결과 파싱
        output_lines = match_result.stdout.strip().split("\n")
        ticket_id = None
        candidates_count = 0
        best_match = None
        similarity = 0.0

        for line in output_lines:
            if line.startswith("TICKET_ID:"):
                ticket_id = line.split(":", 1)[1]
            elif line.startswith("CANDIDATES:"):
                candidates_count = int(line.split(":", 1)[1])
            elif line.startswith("BEST_MATCH:"):
                best_match = line.split(":", 1)[1]
            elif line.startswith("SIMILARITY:"):
                similarity = float(line.split(":", 1)[1])

        print(f"✅ 매칭 완료: {candidates_count}개 후보 발견")
        if best_match:
            print(f"   최고 매칭: {best_match} (유사도: {similarity:.2f})")

        print("\n🎉 티켓 생성 완료!")
        print(f"   티켓 ID: {ticket_id}")
        print(f"   파일 위치: tickets/{ticket_id}.md")
        print("   TICKETS.md: 업데이트됨")

        # 다음 단계 안내
        print("\n💡 다음 단계:")
        print(f"   1. 티켓 검토: tickets/{ticket_id}.md")
        print("   2. 필요시 수동 편집")
        print("   3. 작업 시작 시 상태를 'in_progress'로 변경")

        return 0

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
