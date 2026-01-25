from __future__ import annotations

import re
from pathlib import Path

from ..models import (
    AFOSkillCard,
    ExecutionMode,
    PhilosophyScore,
    SkillCategory,
)

# Trinity Score: 100.0 (Established by Chancellor)
"""
AFO Context7 Intelligence Bridge
Mobilizes external "superpowers" from the awesome-skills repository.
Architecture: Robust "Pseudo-YAML" Parser to handle unquoted colons in descriptions.
"""


def get_context7_intelligence_skills() -> list[AFOSkillCard]:
    """
    Context7 Intelligence Bridge
    Scans external skill libraries and registers them as official AFO Intelligence skills.
    """
    skills = []
    # Relative path resolution from project root
    project_root = Path(__file__).resolve().parents[4]
    base_path = project_root / "packages" / "external"

    # Target repositories for skill harvesting
    targets = [
        base_path / "antigravity-awesome-skills/skills",
        base_path / "claude-code-settings/skills",
    ]

    # Start indexing from 101 to avoid collisions with core skills (1-99)
    skill_idx = 101

    for target_dir in targets:
        if not target_dir.exists():
            continue

        # Iterate through skill directories
        for skill_dir in sorted(target_dir.iterdir()):
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue

            try:
                content = skill_file.read_text(encoding="utf-8")

                # Extract YAML frontmatter block
                # Robust regex for different line endings
                match = re.search(r"---\s*\r?\n(.*?)\r?\n---\s*\r?\n", content, re.DOTALL)
                if not match:
                    # Alternative for missing trailing newline
                    match = re.search(r"---\s*\r?\n(.*?)\r?\n---", content, re.DOTALL)
                    if not match:
                        continue

                yaml_content = match.group(1)

                # Robust "Pseudo-YAML" Parser
                # Handles unquoted colons in descriptions
                data = {}
                for line in yaml_content.split("\n"):
                    if ":" in line:
                        key, val = line.split(":", 1)
                        data[key.strip()] = val.strip().strip('"').strip("'")

                if not data:
                    continue

                name = data.get("name", skill_dir.name)
                description = data.get("description", "No description available.")

                # Sanitize name for skill_id alignment
                safe_name = re.sub(r"[^a-z0-9_]", "_", name.lower())
                skill_id = f"skill_{skill_idx:03d}_{safe_name}"

                # Create the official AFO Skill Card
                card = AFOSkillCard(
                    skill_id=skill_id,
                    name=name,
                    description=description[:1000],
                    category=SkillCategory.INTELLIGENCE,
                    tags=["context7", "superpower", target_dir.parent.name],
                    version="1.0.0",
                    execution_mode=ExecutionMode.SYNC,
                    philosophy_scores=PhilosophyScore(
                        truth=95, goodness=90, beauty=95, serenity=90
                    ),
                    documentation_url=f"file://{skill_file}",
                )

                skills.append(card)
                skill_idx += 1

            except Exception:
                continue

    return skills
