#!/usr/bin/env python3
"""
AFO Kingdom Memory Manager - 메모리 관리 시스템
================================================

제텔카스텐(Zettelkasten) 방법론 기반의 메모리 관리 도구

사용법:
    python memory_manager.py <command> [options]

Commands:
    search <query>      관련 메모리 검색
    session             세션 관리
    fleeting            일시노트 생성
    daily               일일 노트 업데이트
    index               인덱스 재생성
    status              메모리 상태 확인

Examples:
    python memory_manager.py search "security scanner"
    python memory_manager.py session --start
    python memory_manager.py session --save --title "Email 구현" --outcomes "완료"
    python memory_manager.py fleeting "새로운 아이디어: AI 메모리 캐싱"
    python memory_manager.py daily --activity "보안 스캐너 구현" --insight "gh extension 필요"
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# 설정
MEMORY_DIR = Path(__file__).parent.parent / "memory"
DAILY_NOTES_DIR = MEMORY_DIR / "Daily Notes"
SESSIONS_DIR = MEMORY_DIR / "050_Sessions" / datetime.now().strftime("%Y")
FLEETING_DIR = MEMORY_DIR / "040_Fleeting" / "TEMP"
PROJECTS_DIR = MEMORY_DIR / "010_Projects"
KNOWLEDGE_DIR = MEMORY_DIR / "020_Knowledge"

# 디렉토리 생성
for dir_path in [SESSIONS_DIR, FLEETING_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


@dataclass
class Session:
    """세션 데이터"""

    id: str
    title: str
    start_time: datetime
    end_time: datetime | None = None
    outcomes: list[str] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "outcomes": self.outcomes,
            "files_changed": self.files_changed,
            "decisions": self.decisions,
            "insights": self.insights,
        }


class MemoryManager:
    """메모리 관리자"""

    def __init__(self) -> None:
        self.current_session: Session | None = None
        self.session_file: Path | None = None

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """관련 메모리 검색"""
        logger.info(f"🔍 메모리 검색: '{query}'")
        results = []

        # mem MCP 사용
        try:
            # 메모리 검색 (MCP 활용)
            # 실제로는 memory_search_nodes 등의 MCP 도구 사용
            results = self._search_files(query, limit)
        except Exception as e:
            logger.error(f"검색 실패: {e}")

        return results

    def _search_files(self, query: str, limit: int) -> list[dict[str, Any]]:
        """파일 기반 검색 (fallback)"""
        results = []
        keywords = query.lower().split()

        for md_file in MEMORY_DIR.rglob("*.md"):
            if md_file.name.startswith("000_"):
                continue

            try:
                content = md_file.read_text(encoding="utf-8")
                score = sum(1 for kw in keywords if kw in content.lower())

                if score > 0:
                    results.append(
                        {
                            "file": str(md_file.relative_to(MEMORY_DIR)),
                            "score": score,
                            "preview": content[:200].replace("\n", " "),
                        }
                    )
            except Exception:
                continue

        # 점수순 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def start_session(self, title: str) -> str:
        """새 세션 시작"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = Session(
            id=session_id,
            title=title,
            start_time=datetime.now(),
        )
        self.session_file = SESSIONS_DIR / f"{session_id}_{title.replace(' ', '_')}.md"

        # 세션 파일 생성
        self._save_session_file()
        logger.info(f"✅ 세션 시작: {session_id} - {title}")

        return session_id

    def save_session(
        self,
        outcomes: list[str] | None = None,
        files_changed: list[str] | None = None,
        decisions: list[str] | None = None,
        insights: list[str] | None = None,
    ) -> None:
        """현재 세션 저장"""
        if not self.current_session:
            logger.error("❌ 활성 세션이 없습니다. 먼저 --start로 시작하세요.")
            return

        # 데이터 업데이트
        if outcomes:
            self.current_session.outcomes.extend(outcomes)
        if files_changed:
            self.current_session.files_changed.extend(files_changed)
        if decisions:
            self.current_session.decisions.extend(decisions)
        if insights:
            self.current_session.insights.extend(insights)

        self.current_session.end_time = datetime.now()
        self._save_session_file()

        logger.info(f"✅ 세션 저장 완료: {self.current_session.id}")

    def _save_session_file(self) -> None:
        """세션 파일 저장"""
        if not self.current_session or not self.session_file:
            return

        content = f"""---
id: {self.current_session.id}
type: session
title: {self.current_session.title}
start_time: {self.current_session.start_time.isoformat()}
end_time: {self.current_session.end_time.isoformat() if self.current_session.end_time else "ongoing"}
tags:
  - session
  - {datetime.now().strftime("%Y-%m")}
---

# {self.current_session.title}

## 개요
- **세션 ID**: {self.current_session.id}
- **시작**: {self.current_session.start_time.strftime("%Y-%m-%d %H:%M")}
- **종료**: {self.current_session.end_time.strftime("%Y-%m-%d %H:%M") if self.current_session.end_time else "진행중"}

## 성과 (Outcomes)
"""
        for outcome in self.current_session.outcomes:
            content += f"- [x] {outcome}\n"

        if self.current_session.decisions:
            content += "\n## 의사결정 (Decisions)\n"
            for decision in self.current_session.decisions:
                content += f"- 🎯 {decision}\n"

        if self.current_session.insights:
            content += "\n## 인사이트 (Insights)\n"
            for insight in self.current_session.insights:
                content += f"- 💡 {insight}\n"

        if self.current_session.files_changed:
            content += "\n## 변경된 파일\n"
            for file in self.current_session.files_changed:
                content += f"- `{file}`\n"

        content += f"\n---\n*세션 기록 자동 생성됨 | AFO Kingdom Memory System*\n"

        self.session_file.write_text(content, encoding="utf-8")

    def create_fleeting(self, content: str, tags: list[str] | None = None) -> Path:
        """일시노트 생성"""
        timestamp = datetime.now()
        note_id = timestamp.strftime("%Y%m%d_%H%M%S")

        # 키워드 추출 (간단한 방법)
        keywords = content.split()[:3]
        keyword_str = "_".join(kw[:10] for kw in keywords)

        filename = f"{note_id}_{keyword_str}.md"
        filepath = FLEETING_DIR / filename

        note_content = f"""---
id: {note_id}
type: fleeting
created: {timestamp.isoformat()}
tags:
  - fleeting
{chr(10).join(f"  - {tag}" for tag in (tags or []))}
---

# {content[:50]}{"..." if len(content) > 50 else ""}

{content}

---
*일시노트 | 24-48시간 내 정리 필요*
"""

        filepath.write_text(note_content, encoding="utf-8")
        logger.info(f"✅ 일시노트 생성: {filename}")

        return filepath

    def update_daily(self, activity: str, insight: str | None = None) -> None:
        """일일 노트 업데이트"""
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
        weekday = ["월", "화", "수", "목", "금", "토", "일"][today.weekday()]

        daily_file = DAILY_NOTES_DIR / f"{date_str}_{weekday}.md"

        # 파일이 없으면 생성
        if not daily_file.exists():
            self._create_daily_note(daily_file, today, date_str, weekday)

        # 내용 추가
        timestamp = today.strftime("%H:%M")
        entry = f"\n- [{timestamp}] {activity}"
        if insight:
            entry += f"\n  - 💡 {insight}"

        with open(daily_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

        logger.info(f"✅ 일일 노트 업데이트: {daily_file.name}")

    def _create_daily_note(
        self, filepath: Path, today: datetime, date_str: str, weekday: str
    ) -> None:
        """새 일일 노트 생성"""
        content = f"""---
date: {date_str}
weekday: {weekday}
type: daily
tags:
  - daily
---

# {date_str} ({weekday})요일

## 🌅 아침
- [ ] Trinity Score 확인
- [ ] 오늘의 목표 설정

## 📝 활동 로그
"""
        filepath.write_text(content, encoding="utf-8")

    def status(self) -> None:
        """메모리 상태 확인"""
        logger.info("📊 메모리 시스템 상태")
        logger.info("=" * 50)

        # 통계 수집
        stats = {
            "total_notes": len(list(MEMORY_DIR.rglob("*.md"))),
            "daily_notes": len(list(DAILY_NOTES_DIR.glob("*.md"))),
            "fleeting_notes": len(list(FLEETING_DIR.glob("*.md"))),
            "sessions": len(list(SESSIONS_DIR.glob("*.md"))),
            "projects": len([d for d in PROJECTS_DIR.iterdir() if d.is_dir()]),
        }

        logger.info(f"  📚 전체 노트: {stats['total_notes']}개")
        logger.info(f"  📅 일일 노트: {stats['daily_notes']}개")
        logger.info(f"  📝 일시노트: {stats['fleeting_notes']}개")
        logger.info(f"  🎯 세션: {stats['sessions']}개")
        logger.info(f"  📁 프로젝트: {stats['projects']}개")

        # 현재 세션
        if self.current_session:
            logger.info(f"\n  🟢 활성 세션: {self.current_session.title}")
            duration = datetime.now() - self.current_session.start_time
            logger.info(f"     진행 시간: {duration.seconds // 60}분")

    def get_recent_sessions(self, limit: int = 3) -> list[dict[str, Any]]:
        """최근 세션 목록"""
        sessions = []
        for session_file in sorted(SESSIONS_DIR.glob("*.md"), reverse=True)[:limit]:
            try:
                content = session_file.read_text(encoding="utf-8")
                # 간단한 파싱
                title = ""
                for line in content.split("\n"):
                    if line.startswith("# "):
                        title = line[2:]
                        break

                sessions.append(
                    {
                        "file": session_file.name,
                        "title": title,
                        "date": session_file.name[:8],
                    }
                )
            except Exception:
                continue

        return sessions


def main() -> int:
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="AFO Kingdom Memory Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    # 메모리 검색
    python memory_manager.py search "security scanner"
    
    # 세션 관리
    python memory_manager.py session --start --title "보안 구현"
    python memory_manager.py session --save --outcomes "Email 알림 완료"
    
    # 일시노트
    python memory_manager.py fleeting "새로운 아이디어"
    
    # 일일 노트
    python memory_manager.py daily --activity "코드 리뷰" --insight "리팩토링 필요"
    
    # 상태 확인
    python memory_manager.py status
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="명령어")

    # search
    search_parser = subparsers.add_parser("search", help="메모리 검색")
    search_parser.add_argument("query", help="검색어")
    search_parser.add_argument("--limit", type=int, default=5, help="결과 수")

    # session
    session_parser = subparsers.add_parser("session", help="세션 관리")
    session_parser.add_argument("--start", action="store_true", help="새 세션 시작")
    session_parser.add_argument("--save", action="store_true", help="세션 저장")
    session_parser.add_argument("--title", help="세션 제목")
    session_parser.add_argument("--outcomes", nargs="+", help="성과 목록")
    session_parser.add_argument("--files", nargs="+", help="변경된 파일")
    session_parser.add_argument("--decisions", nargs="+", help="의사결정")
    session_parser.add_argument("--insights", nargs="+", help="인사이트")

    # fleeting
    fleeting_parser = subparsers.add_parser("fleeting", help="일시노트 생성")
    fleeting_parser.add_argument("content", help="노트 내용")
    fleeting_parser.add_argument("--tags", nargs="+", help="태그")

    # daily
    daily_parser = subparsers.add_parser("daily", help="일일 노트 업데이트")
    daily_parser.add_argument("--activity", required=True, help="활동 내용")
    daily_parser.add_argument("--insight", help="인사이트")

    # status
    subparsers.add_parser("status", help="메모리 상태 확인")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    manager = MemoryManager()

    if args.command == "search":
        results = manager.search(args.query, args.limit)
        if results:
            print(f"\n🔍 '{args.query}' 검색 결과:")
            print("=" * 60)
            for i, r in enumerate(results, 1):
                print(f"\n{i}. {r['file']} (관련도: {r['score']})")
                print(f"   {r['preview']}...")
        else:
            print(f"❌ '{args.query}'에 대한 결과 없음")

    elif args.command == "session":
        if args.start:
            if not args.title:
                print("❌ --title 필수")
                return 1
            manager.start_session(args.title)
        elif args.save:
            manager.save_session(
                outcomes=args.outcomes,
                files_changed=args.files,
                decisions=args.decisions,
                insights=args.insights,
            )
        else:
            # 최근 세션 표시
            sessions = manager.get_recent_sessions()
            print("\n🎯 최근 세션:")
            for s in sessions:
                print(f"  - [{s['date']}] {s['title']}")

    elif args.command == "fleeting":
        filepath = manager.create_fleeting(args.content, args.tags)
        print(f"✅ 생성됨: {filepath}")

    elif args.command == "daily":
        manager.update_daily(args.activity, args.insight)

    elif args.command == "status":
        manager.status()

    return 0


if __name__ == "__main__":
    sys.exit(main())
