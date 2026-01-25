#!/usr/bin/env python3
"""
Add shield decorator to AFO Kingdom Router files.

This script automatically adds the shield decorator to all router endpoints
that don't already have it. Supports DRY_RUN mode for safe testing.

Usage:
    python scripts/add_shield_to_routers.py --dry-run    # Preview changes
    python scripts/add_shield_to_routers.py --apply       # Apply changes
    python scripts/add_shield_to_routers.py --list         # List routers without shield

Priority Categories:
    1. PII/Security: external_router.py, public_sandbox_router.py
    2. Core API: root.py, chancellor_router.py
    3. Integration: n8n.py, discord_router.py, kakao_router.py
    4. Analytics: client_stats.py, log_analysis.py
    5. UI Generation: gen_ui.py, gen_ui_new.py
    6. Knowledge: rag_query.py, personae.py
    7. Collaboration: council.py, matrix.py
    8. AI/Agents: ai_diagram.py, multimodal.py
    9. Utilities: remaining files
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Router files that already have shield applied
APPLIED_ROUTERS = {
    "trinity.py",
    "health.py",
    "ssot.py",
    "julie_royal.py",
    "users.py",
    "aicpa.py",
    "auth.py",
    "finance.py",
    "finance_root.py",
    "budget.py",
}

# Priority categorization for pillar assignment
PRIORITY_CATEGORIES: Dict[str, List[str]] = {
    "PII/Security": [
        "external_router.py",
        "public_sandbox_router.py",
    ],
    "Core API": [
        "root.py",
        "chancellor_router.py",
    ],
    "Integration": [
        "n8n.py",
        "discord_router.py",
        "kakao_router.py",
    ],
    "Analytics": [
        "client_stats.py",
        "log_analysis.py",
    ],
    "UI Generation": [
        "gen_ui.py",
        "gen_ui_new.py",
    ],
    "Knowledge": [
        "rag_query.py",
        "personas.py",
    ],
    "Collaboration": [
        "council.py",
        "matrix.py",
    ],
    "AI/Agents": [
        "ai_diagram.py",
        "multimodal.py",
    ],
    "Utilities": [
        "cache.py",
        "collaboration.py",
        "compat.py",
        "core_analysis.py",
        "debugging.py",
        "decree_router.py",
        "evolution_router.py",
        "family.py",
        "got.py",
        "grok_stream.py",
        "intake.py",
        "learning_log_router.py",
        "learning_pipeline.py",
        "modal_data.py",
        "multi_agent.py",
        "skills.py",
        "thoughts.py",
        "trinity_debate.py",
        "voice.py",
    ],
}

# Pillar assignment based on category
CATEGORY_TO_PILLAR: Dict[str, str] = {
    "PII/Security": "善",
    "Core API": "眞",
    "Integration": "善",
    "Analytics": "美",
    "UI Generation": "美",
    "Knowledge": "眞",
    "Collaboration": "美",
    "AI/Agents": "眞",
    "Utilities": "善",
}


class ShieldApplicator:
    """Automatically add shield decorator to Router files."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.routers_dir = Path("packages/afo-core/api/routers")
        self.shield_import = "from AFO.utils.standard_shield import shield"
        self.changes_made: Dict[str, int] = {}

    def get_routers_without_shield(self) -> List[Path]:
        """Get list of router files that don't have shield applied."""
        routers = []
        for router_file in self.routers_dir.glob("*.py"):
            if router_file.name not in APPLIED_ROUTERS and router_file.name != "__init__.py":
                routers.append(router_file)
        return sorted(routers)

    def has_shield_import(self, content: str) -> bool:
        """Check if shield import is already present."""
        return "from AFO.utils.standard_shield import shield" in content

    def find_route_decorators(self, content: str) -> List[Tuple[int, str]]:
        """Find all @router.* decorators in the file."""
        pattern = r'(@router\.[^(]+\([^)]*\))'
        matches = []
        lines = content.split("\n")
        
        for i, line in enumerate(lines, 1):
            if "@router" in line:
                matches.append((i, line.strip()))
        
        return matches

    def add_shield_import_if_missing(self, content: str) -> str:
        """Add shield import if not present."""
        if self.has_shield_import(content):
            return content
        
        # Find the last import statement
        lines = content.split("\n")
        last_import_idx = -1
        
        for i, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                last_import_idx = i
        
        if last_import_idx >= 0:
            lines.insert(last_import_idx + 1, "")
            lines.insert(last_import_idx + 2, self.shield_import)
            return "\n".join(lines)
        
        # No imports found, add at the top
        return self.shield_import + "\n\n" + content

    def apply_shield_to_endpoint(
        self,
        content: str,
        route_decorator: str,
        pillar: str,
    ) -> Tuple[str, bool]:
        """Add shield decorator to a specific endpoint."""
        # Check if shield is already present
        if "@shield" in content.split(route_decorator)[0][-100:]:
            return content, False
        
        # Add shield decorator before the route decorator
        shield_decorator = "@shield(pillar=\"" + pillar + "\")\n"
        return content.replace(route_decorator, shield_decorator + route_decorator), True

    def process_router_file(self, router_file: Path) -> bool:
        """Process a single router file."""
        content = router_file.read_text(encoding="utf-8")
        original_content = content
        
        # Determine pillar based on category
        pillar = "善"  # Default
        for category, routers in PRIORITY_CATEGORIES.items():
            if router_file.name in routers:
                pillar = CATEGORY_TO_PILLAR[category]
                break
        
        # Add shield import if missing
        content = self.add_shield_import_if_missing(content)
        
        # Find and shield all route decorators
        route_decorators = self.find_route_decorators(content)
        changes = 0
        
        for line_num, decorator in route_decorators:
            content, changed = self.apply_shield_to_endpoint(content, decorator, pillar)
            if changed:
                changes += 1
        
        if changes > 0 and content != original_content:
            if self.dry_run:
                print(f"[DRY_RUN] {router_file.name}: {changes} endpoints would be shielded")
                self.changes_made[router_file.name] = changes
                return False
            else:
                # Backup original file
                backup_file = router_file.with_suffix(f"{router_file.suffix}.backup")
                router_file.rename(backup_file)
                
                # Write modified content
                router_file.write_text(content, encoding="utf-8")
                print(f"[APPLIED] {router_file.name}: {changes} endpoints shielded")
                self.changes_made[router_file.name] = changes
                return True
        
        return False

    def process_all_routers(self) -> Dict[str, int]:
        """Process all routers that don't have shield."""
        routers = self.get_routers_without_shield()
        
        print(f"\n{'=' * 60}")
        print(f"Processing {len(routers)} router files...")
        print(f"Mode: {'DRY_RUN (no changes)' if self.dry_run else 'APPLY (changes will be made)'}")
        print(f"{'=' * 60}\n")
        
        for router_file in routers:
            self.process_router_file(router_file)
        
        return self.changes_made

    def list_routers_by_priority(self) -> None:
        """List routers organized by priority category."""
        routers = self.get_routers_without_shield()
        
        print(f"\n{'=' * 60}")
        print(f"Routers without shield ({len(routers)} files):")
        print(f"{'=' * 60}\n")
        
        for category, router_files in PRIORITY_CATEGORIES.items():
            category_routers = [r for r in routers if r.name in router_files]
            if category_routers:
                pillar = CATEGORY_TO_PILLAR[category]
                print(f"[{category}] - pillar: {pillar}")
                for router in category_routers:
                    print(f"  - {router.name}")
                print()


def main():
    parser = argparse.ArgumentParser(
        description="Add shield decorator to AFO Kingdom Router files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without modifying files (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Apply changes to files (creates backups)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        default=False,
        help="List routers without shield, organized by priority",
    )
    
    args = parser.parse_args()
    
    if args.list:
        applicator = ShieldApplicator(dry_run=True)
        applicator.list_routers_by_priority()
        return
    
    if not args.apply:
        args.dry_run = True
    
    applicator = ShieldApplicator(dry_run=args.dry_run)
    changes = applicator.process_all_routers()
    
    if changes:
        print(f"\n{'=' * 60}")
        print(f"Summary: {sum(changes.values())} endpoints across {len(changes)} files")
        print(f"{'=' * 60}")
        
        if args.dry_run:
            print("\nRun with --apply to apply these changes.")
    else:
        print("\nNo changes needed.")


if __name__ == "__main__":
    main()