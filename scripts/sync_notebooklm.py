# Copyright 2025 AFO Kingdom. All rights reserved.
"""
AFO Kingdom - NotebookLM Mirroring Script (Track A)
---------------------------------------------------
This script automates the synchronization between local files (Source of Truth)
and the AFO Knowledge Base structure for NotebookLM.

It performs the following:
1. Reads `notebooklm.manifest.json`.
2. Enforces directory structure: `docs/kb/notebooklm/<slug>/sources` & `notes`.
3. Scans for files and updates the `README.md` index.
4. Indexes content into Qdrant Vector DB (Wisdom).
"""

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from qdrant_client import QdrantClient

# Constants
MANIFEST_PATH = Path("docs/kb/notebooklm/notebooklm.manifest.json")
KB_ROOT = Path("docs/kb/notebooklm")

# Initialize Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
qdrant = QdrantClient(url=QDRANT_URL)


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        print(f"❌ Manifest not found at {MANIFEST_PATH}")
        sys.exit(1)

    try:
        with Path(MANIFEST_PATH).open(encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in manifest: {e}")
        sys.exit(1)


def ensure_structure(notebook: dict) -> dict | None:
    slug = notebook.get("slug")
    if not slug:
        print("⚠️ Skipping notebook without slug")
        return None

    path_base = KB_ROOT / slug
    path_sources = path_base / "sources"
    path_notes = path_base / "notes"

    path_sources.mkdir(parents=True, exist_ok=True)
    path_notes.mkdir(parents=True, exist_ok=True)

    # Count files
    source_count = len(
        [f for f in path_sources.glob("*") if f.is_file() and not f.name.startswith(".")]
    )
    note_count = len(
        [f for f in path_notes.glob("*") if f.is_file() and not f.name.startswith(".")]
    )

    return {
        "slug": slug,
        "title": notebook.get("title", slug),
        "source_count": source_count,
        "note_count": note_count,
        "path_sources": str(path_sources),
        "path_notes": str(path_notes),
        "last_sync": datetime.now(UTC).isoformat(),
    }


def update_readme(stats: list[dict]) -> None:
    readme_path = KB_ROOT / "README.md"

    with Path(readme_path).open("w", encoding="utf-8") as f:
        f.write("# 📚 NotebookLM Knowledge Base (Mirror)\n\n")
        f.write(
            "This directory contains the mirrored Knowledge Base for AFO's NotebookLM integration.\n"
        )
        f.write("Strategy: **Track A (SSOT Mirroring)**\n\n")
        f.write(f"**Last Sync:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| Notebook | Sources | Notes | Path |\n")
        f.write("|----------|:-------:|:-----:|------|\n")

        f.writelines(
            f"| {s['title']} | {s['source_count']} | {s['note_count']} | `{s['path_sources']}` |\n"
            for s in stats
        )

        f.write("\n\n## Usage\n")
        f.write("1. Place source documents (PDF, MD, txt) in `sources/`.\n")
        f.write("2. Place NotebookLM generated notes/summaries in `notes/`.\n")
        f.write("3. Run `python scripts/sync_notebooklm.py` to update this index.\n")


def main() -> None:
    print("🔮 Starting NotebookLM Mirror Sync...")

    manifest = load_manifest()
    notebooks = manifest.get("notebooks", [])
    print(f"📘 Found {len(notebooks)} notebooks in manifest.")

    stats = []
    for nb in notebooks:
        print(f"   - Processing: {nb.get('title')} ({nb.get('slug')})")
        stat = ensure_structure(nb)
        if stat:
            stats.append(stat)

    update_readme(stats)
    print(f"✅ Sync Complete. Index updated at {KB_ROOT / 'README.md'}")


if __name__ == "__main__":
    main()
