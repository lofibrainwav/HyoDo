#!/usr/bin/env python3
"""
AFO Kingdom Memory Manager -   
================================================

(Zettelkasten)     

:
    python memory_manager.py <command> [options]

Commands:
    search <query>        
    session              
    fleeting             
    daily                 
    index                
    status                

Examples:
    python memory_manager.py search "security scanner"
    python memory_manager.py session --start
    python memory_manager.py session --save --title "Email " --outcomes ""
    python memory_manager.py fleeting " : AI  "
    python memory_manager.py daily --activity "  " --insight "gh extension "
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

# 
MEMORY_DIR = Path(__file__).parent.parent / "memory"
DAILY_NOTES_DIR = MEMORY_DIR / "Daily Notes"
SESSIONS_DIR = MEMORY_DIR / "050_Sessions" / datetime.now().strftime("%Y")
FLEETING_DIR = MEMORY_DIR / "040_Fleeting" / "TEMP"
PROJECTS_DIR = MEMORY_DIR / "010_Projects"
KNOWLEDGE_DIR = MEMORY_DIR / "020_Knowledge"

#  
for dir_path in [SESSIONS_DIR, FLEETING_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


@dataclass
class Session:
    """ """

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
    """ """

    def __init__(self) -> None:
        self.current_session: Session | None = None
        self.session_file: Path | None = None

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """  """
        logger.info(f"🔍  : '{query}'")
        results = []

        # mem MCP 
        try:
            #   (MCP )
            #  memory_search_nodes  MCP  
            results = self._search_files(query, limit)
        except Exception as e:
            logger.error(f" : {e}")

        return results

    def _search_files(self, query: str, limit: int) -> list[dict[str, Any]]:
        """   (fallback)"""
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

        #  
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def start_session(self, title: str) -> str:
        """  """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = Session(
            id=session_id,
            title=title,
            start_time=datetime.now(),
        )
        self.session_file = SESSIONS_DIR / f"{session_id}_{title.replace(' ', '_')}.md"

        #   
        self._save_session_file()
        logger.info(f"✅  : {session_id} - {title}")

        return session_id

    def save_session(
        self,
        outcomes: list[str] | None = None,
        files_changed: list[str] | None = None,
        decisions: list[str] | None = None,
        insights: list[str] | None = None,
    ) -> None:
        """  """
        if not self.current_session:
            logger.error("❌   .  --start .")
            return

        #  
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

        logger.info(f"✅   : {self.current_session.id}")

    def _save_session_file(self) -> None:
        """  """
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

## 
- ** ID**: {self.current_session.id}
- ****: {self.current_session.start_time.strftime("%Y-%m-%d %H:%M")}
- ****: {self.current_session.end_time.strftime("%Y-%m-%d %H:%M") if self.current_session.end_time else ""}

##  (Outcomes)
"""
        for outcome in self.current_session.outcomes:
            content += f"- [x] {outcome}\n"

        if self.current_session.decisions:
            content += "\n##  (Decisions)\n"
            for decision in self.current_session.decisions:
                content += f"- 🎯 {decision}\n"

        if self.current_session.insights:
            content += "\n##  (Insights)\n"
            for insight in self.current_session.insights:
                content += f"- 💡 {insight}\n"

        if self.current_session.files_changed:
            content += "\n##  \n"
            for file in self.current_session.files_changed:
                content += f"- `{file}`\n"

        content += f"\n---\n*    | AFO Kingdom Memory System*\n"

        self.session_file.write_text(content, encoding="utf-8")

    def create_fleeting(self, content: str, tags: list[str] | None = None) -> Path:
        """ """
        timestamp = datetime.now()
        note_id = timestamp.strftime("%Y%m%d_%H%M%S")

        #   ( )
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
* | 24-48   *
"""

        filepath.write_text(note_content, encoding="utf-8")
        logger.info(f"✅  : {filename}")

        return filepath

    def update_daily(self, activity: str, insight: str | None = None) -> None:
        """  """
        today = datetime.now()
        date_str = today.strftime("%Y-%m-%d")
        weekday = ["", "", "", "", "", "", ""][today.weekday()]

        daily_file = DAILY_NOTES_DIR / f"{date_str}_{weekday}.md"

        #   
        if not daily_file.exists():
            self._create_daily_note(daily_file, today, date_str, weekday)

        #  
        timestamp = today.strftime("%H:%M")
        entry = f"\n- [{timestamp}] {activity}"
        if insight:
            entry += f"\n  - 💡 {insight}"

        with open(daily_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

        logger.info(f"✅   : {daily_file.name}")

    def _create_daily_note(
        self, filepath: Path, today: datetime, date_str: str, weekday: str
    ) -> None:
        """   """
        content = f"""---
date: {date_str}
weekday: {weekday}
type: daily
tags:
  - daily
---

# {date_str} ({weekday})

## 🌅 
- [ ] Trinity Score 
- [ ]   

## 📝  
"""
        filepath.write_text(content, encoding="utf-8")

    def status(self) -> None:
        """  """
        logger.info("📊   ")
        logger.info("=" * 50)

        #  
        stats = {
            "total_notes": len(list(MEMORY_DIR.rglob("*.md"))),
            "daily_notes": len(list(DAILY_NOTES_DIR.glob("*.md"))),
            "fleeting_notes": len(list(FLEETING_DIR.glob("*.md"))),
            "sessions": len(list(SESSIONS_DIR.glob("*.md"))),
            "projects": len([d for d in PROJECTS_DIR.iterdir() if d.is_dir()]),
        }

        logger.info(f"  📚  : {stats['total_notes']}")
        logger.info(f"  📅  : {stats['daily_notes']}")
        logger.info(f"  📝 : {stats['fleeting_notes']}")
        logger.info(f"  🎯 : {stats['sessions']}")
        logger.info(f"  📁 : {stats['projects']}")

        #  
        if self.current_session:
            logger.info(f"\n  🟢  : {self.current_session.title}")
            duration = datetime.now() - self.current_session.start_time
            logger.info(f"      : {duration.seconds // 60}")

    def get_recent_sessions(self, limit: int = 3) -> list[dict[str, Any]]:
        """  """
        sessions = []
        for session_file in sorted(SESSIONS_DIR.glob("*.md"), reverse=True)[:limit]:
            try:
                content = session_file.read_text(encoding="utf-8")
                #  
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
    """ """
    parser = argparse.ArgumentParser(
        description="AFO Kingdom Memory Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
:
    #  
    python memory_manager.py search "security scanner"
    
    #  
    python memory_manager.py session --start --title " "
    python memory_manager.py session --save --outcomes "Email  "
    
    # 
    python memory_manager.py fleeting " "
    
    #  
    python memory_manager.py daily --activity " " --insight " "
    
    #  
    python memory_manager.py status
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="")

    # search
    search_parser = subparsers.add_parser("search", help=" ")
    search_parser.add_argument("query", help="")
    search_parser.add_argument("--limit", type=int, default=5, help=" ")

    # session
    session_parser = subparsers.add_parser("session", help=" ")
    session_parser.add_argument("--start", action="store_true", help="  ")
    session_parser.add_argument("--save", action="store_true", help=" ")
    session_parser.add_argument("--title", help=" ")
    session_parser.add_argument("--outcomes", nargs="+", help=" ")
    session_parser.add_argument("--files", nargs="+", help=" ")
    session_parser.add_argument("--decisions", nargs="+", help="")
    session_parser.add_argument("--insights", nargs="+", help="")

    # fleeting
    fleeting_parser = subparsers.add_parser("fleeting", help=" ")
    fleeting_parser.add_argument("content", help=" ")
    fleeting_parser.add_argument("--tags", nargs="+", help="")

    # daily
    daily_parser = subparsers.add_parser("daily", help="  ")
    daily_parser.add_argument("--activity", required=True, help=" ")
    daily_parser.add_argument("--insight", help="")

    # status
    subparsers.add_parser("status", help="  ")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    manager = MemoryManager()

    if args.command == "search":
        results = manager.search(args.query, args.limit)
        if results:
            print(f"\n🔍 '{args.query}'  :")
            print("=" * 60)
            for i, r in enumerate(results, 1):
                print(f"\n{i}. {r['file']} (: {r['score']})")
                print(f"   {r['preview']}...")
        else:
            print(f"❌ '{args.query}'   ")

    elif args.command == "session":
        if args.start:
            if not args.title:
                print("❌ --title ")
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
            #   
            sessions = manager.get_recent_sessions()
            print("\n🎯  :")
            for s in sessions:
                print(f"  - [{s['date']}] {s['title']}")

    elif args.command == "fleeting":
        filepath = manager.create_fleeting(args.content, args.tags)
        print(f"✅ : {filepath}")

    elif args.command == "daily":
        manager.update_daily(args.activity, args.insight)

    elif args.command == "status":
        manager.status()

    return 0


if __name__ == "__main__":
    sys.exit(main())
