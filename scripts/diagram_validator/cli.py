#!/usr/bin/env python3
"""
Diagram Validator CLI - Command-line interface

Usage:
    python scripts/validate_diagram_schema.py [--strict] [--pillar-check] [path]
    python -m scripts.diagram_validator.cli [options]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from scripts.diagram_validator.models import ValidationSummary
from scripts.diagram_validator.validator import DiagramSchemaValidator

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def print_summary(summary: ValidationSummary) -> None:
    """Print validation summary to stdout."""
    print("\n" + "=" * 60)
    print("DIAGRAM SCHEMA VALIDATION SUMMARY")
    print("=" * 60)

    status = "PASS" if summary.all_passed else "FAIL"
    print(f"Status: {status}")
    print(f"Files checked: {summary.total_files}")
    print(f"Passed: {summary.passed_files}")
    print(f"Failed: {summary.failed_files}")
    print(f"Total errors: {summary.total_errors}")
    print(f"Total warnings: {summary.total_warnings}")

    if summary.results:
        print("\nDetails:")
        print("-" * 60)
        for result in summary.results:
            icon = "[OK]" if result.is_valid else "[FAIL]"
            print(f"{icon} {result.file_path}")
            for issue in result.issues:
                print(f"    {issue}")

            if result.pillar_nodes_found:
                print(f"    Pillar nodes found: {', '.join(result.pillar_nodes_found)}")

    print("=" * 60)


def main() -> int:
    """Main entry point for CLI execution.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Validate Excalidraw diagram schemas for AFO Kingdom",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Validate all diagrams in docs/diagrams/
    python scripts/validate_diagram_schema.py

    # Validate with strict naming enforcement
    python scripts/validate_diagram_schema.py --strict

    # Validate with pillar node checking
    python scripts/validate_diagram_schema.py --pillar-check

    # Validate a specific directory
    python scripts/validate_diagram_schema.py path/to/diagrams/
        """,
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="docs/diagrams",
        help="Directory to validate (default: docs/diagrams)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat naming convention warnings as errors",
    )
    parser.add_argument(
        "--pillar-check",
        action="store_true",
        help="Validate that diagrams contain required pillar nodes",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="Path to SSOT_VISUAL_MANIFEST.txt (default: auto-detect in target directory)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print summary, not individual issues",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose output including skipped files",
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    # Resolve paths
    base_path = Path(args.path)
    manifest_path = Path(args.manifest) if args.manifest else base_path / "SSOT_VISUAL_MANIFEST.txt"

    # Handle non-existent directory gracefully
    if not base_path.exists():
        print(f"Directory not found: {base_path}, skipping diagram validation.")
        return 0

    # Create validator and run
    validator = DiagramSchemaValidator(
        strict=args.strict,
        pillar_check=args.pillar_check,
    )

    summary = validator.validate_directory(base_path, manifest_path)

    # Print results
    if not args.quiet or not summary.all_passed:
        print_summary(summary)

    return 0 if summary.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
