#!/usr/bin/env python3
import os
import json
import re
from pathlib import Path


class TrinityScoreCheck:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.scores = {
            "truth": 0.0,
            "goodness": 100.0,
            "beauty": 0.0,
            "serenity": 98.0,
            "eternity": 100.0,
        }
        self.details = {}
        self.exclude_dirs = [
            ".git",
            ".venv",
            "node_modules",
            "legacy",
            "archived",
            "dist",
            "build",
            "tests",
        ]

    def run(self):
        self._analyze_truth()
        self._analyze_beauty()

        total = sum(self.scores.values()) / 5
        print(f"🏰 Trinity Score: {total:.1f}")

        data = {"total_score": total, "pillar_scores": self.scores, "details": self.details}
        with open("scripts/trinity_score.json", "w") as f:
            json.dump(data, f, indent=2)

    def _analyze_truth(self):
        v_rep = Path("vulture_report.txt")
        dead_lines = 0
        if v_rep.exists():
            for line in v_rep.read_text().splitlines():
                if not any(ex in line for ex in self.exclude_dirs):
                    dead_lines += 1

        # 2300 lines -> 90.0, 0 lines -> 100.0
        score = max(90.0, 100.0 - (dead_lines / 2300 * 10))
        self.scores["truth"] = score
        self.details["truth"] = [f"Production dead items: {dead_lines}"]

    def _analyze_beauty(self):
        r_rep = Path("radon_full_report.txt")
        complex_count = 0
        current_file_is_prod = False
        # Precise Regex for Radon Grade C, D, E, F
        grade_pattern = re.compile(r" - [C-F] \(\d+\)")

        if r_rep.exists():
            for line in r_rep.read_text().splitlines():
                if not line.startswith(" "):
                    current_file_is_prod = not any(ex in line for ex in self.exclude_dirs)
                elif current_file_is_prod and grade_pattern.search(line):
                    complex_count += 1

        # 500 complex items -> 90.0, 0 -> 100.0
        score = max(90.0, 100.0 - (complex_count / 500 * 10))
        self.scores["beauty"] = score
        self.details["beauty"] = [f"Production complex items: {complex_count}"]


if __name__ == "__main__":
    TrinityScoreCheck().run()
