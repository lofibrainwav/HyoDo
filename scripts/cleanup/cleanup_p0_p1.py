#!/usr/bin/env python3
"""
AFO Kingdom Cleanup Script - P0/P1 Issues
Handles: nested packages, misplaced files, pycache, venvs, WARP.md
"""

import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(".")
QUARANTINE = ROOT / "quarantine" / "_cleanup_phase22"
QUARANTINE.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

print("=" * 60)
print("AFO Kingdom Cleanup - P0/P1")
print("=" * 60)

# P0-1: Nested packages/packages
nested_packages = ROOT / "packages" / "packages"
if nested_packages.exists():
    target = QUARANTINE / f"packages_packages_{timestamp}"
    print(f"✓ Moving {nested_packages} -> {target}")
    shutil.move(str(nested_packages), str(target))
else:
    print("✓ No nested packages/packages (good)")

# P0-2: Root misplaced files (Git tracked)
misplaced_files = ["julie_logs.db", "kingdom_dashboard.js", "kingdom_dashboard.css"]
for fname in misplaced_files:
    fpath = ROOT / fname
    if fpath.exists():
        # Remove from git first
        result = subprocess.run(
            ["git", "rm", "--cached", str(fpath)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        target = QUARANTINE / fname
        print(f"✓ Git rm --cached {fname} (exit {result.returncode})")
        shutil.move(str(fpath), str(target))
        print(f"✓ Moved {fname} -> quarantine/")

# P0-3: Root __pycache__
root_pycache = ROOT / "__pycache__"
if root_pycache.exists():
    shutil.rmtree(root_pycache)
    print("✓ Removed root __pycache__/")

# P0-4: All __pycache__ in repo (excluding venvs)
print("✓ Scanning for __pycache__ directories...")
count = 0
for pycache in ROOT.rglob("__pycache__"):
    # Skip if inside venv
    if ".venv" in str(pycache) or "venv_" in str(pycache):
        continue
    shutil.rmtree(pycache, ignore_errors=True)
    count += 1
print(f"✓ Removed {count} __pycache__ directories")

# P1-1: Unused venvs
venvs_to_remove = ["venv_musicgen", "venv_afo_music"]
for venv_name in venvs_to_remove:
    venv_path = ROOT / venv_name
    if venv_path.exists():
        print(f"✓ Removing {venv_name}... (this may take a moment)")
        shutil.rmtree(venv_path)
        print(f"✓ Removed {venv_name}")

# P1-2: WARP.md (symlink) - remove since it's untracked
warp_md = ROOT / "WARP.md"
if warp_md.exists() or warp_md.is_symlink():
    warp_md.unlink()
    print("✓ Removed WARP.md symlink")

# Update .gitignore
gitignore = ROOT / ".gitignore"
additions = [
    "",
    "# Cleanup phase 22 - additional exclusions",
    "julie_logs.db",
    "kingdom_dashboard.js",
    "kingdom_dashboard.css",
    "__pycache__/",
    "venv_musicgen/",
    "venv_afo_music/",
]

with gitignore.open("a") as f:
    f.write("\n".join(additions) + "\n")
print("✓ Updated .gitignore")

print("\n" + "=" * 60)
print("Cleanup complete!")
print(f"Quarantined files: {QUARANTINE}")
print("=" * 60)
print("\nNext steps:")
print("1. Review git status")
print("2. Run quality gates: make lint && make test")
print("3. Commit changes")
