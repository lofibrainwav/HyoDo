#!/usr/bin/env python3
"""
Type Coverage Checker for AFO Kingdom

This script analyzes Python files in the packages/ directory and calculates
type hint coverage metrics to track progress toward 100% type safety.
"""

import ast
import sys
from pathlib import Path


class TypeCoverageAnalyzer:
    """Analyzes type hint coverage in Python files."""

    def __init__(self, package_dir: str = "packages") -> None:
        self.package_dir = Path(package_dir)
        self.stats = {
            "total_files": 0,
            "total_functions": 0,
            "typed_functions": 0,
            "total_classes": 0,
            "typed_classes": 0,
            "coverage_percent": 0.0,
        }

    def analyze_file(self, file_path: Path) -> tuple[int, int]:
        """Analyze a single Python file for type hints."""
        try:
            content = Path(file_path).read_text(encoding="utf-8")

            tree = ast.parse(content)

            total_functions = 0
            typed_functions = 0

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    total_functions += 1
                    # Check if function has return type annotation
                    if node.returns is not None:
                        typed_functions += 1

            return total_functions, typed_functions

        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not analyze {file_path}: {e}", file=sys.stderr)
            return 0, 0

    def analyze_package(self) -> dict[str, any]:
        """Analyze all Python files in the package directory."""
        python_files = list(self.package_dir.rglob("*.py"))

        if not python_files:
            print(f"No Python files found in {self.package_dir}")
            return self.stats

        print(f"🔍 Analyzing {len(python_files)} Python files...")

        for file_path in python_files:
            if file_path.name.startswith("__") and file_path.name.endswith("__.py"):
                continue  # Skip __init__.py files

            functions, typed = self.analyze_file(file_path)
            self.stats["total_functions"] += functions
            self.stats["typed_functions"] += typed

        # Calculate coverage
        if self.stats["total_functions"] > 0:
            self.stats["coverage_percent"] = (
                self.stats["typed_functions"] / self.stats["total_functions"] * 100
            )

        return self.stats

    def print_report(self) -> None:
        """Print a formatted coverage report."""
        print("\n" + "=" * 60)
        print("🎯 AFO Kingdom Type Coverage Report")
        print("=" * 60)

        print(f"📁 Package Directory: {self.package_dir}")
        print(f"📊 Total Functions: {self.stats['total_functions']:,}")
        print(f"✅ Typed Functions: {self.stats['typed_functions']:,}")
        print(f"📈 Coverage: {self.stats['coverage_percent']:.1f}%")
        # Progress bar
        bar_width = 40
        filled = int(bar_width * self.stats["coverage_percent"] / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"📈 Progress: [{bar}]")

        # Assessment
        if self.stats["coverage_percent"] >= 90:
            status = "🎉 Excellent (Ready for strict mode)"
            color = "🟢"
        elif self.stats["coverage_percent"] >= 70:
            status = "👍 Good (Phase 2 target achieved)"
            color = "🟡"
        elif self.stats["coverage_percent"] >= 50:
            status = "⚠️  Fair (Needs improvement)"
            color = "🟠"
        else:
            status = "❌ Poor (Immediate action needed)"
            color = "🔴"

        print(f"🏆 Status: {color} {status}")

        # Recommendations
        print("\n💡 Recommendations:")
        if self.stats["coverage_percent"] < 80:
            remaining = int(self.stats["total_functions"] * 0.8 - self.stats["typed_functions"])
            print(f"   • Add type hints to ~{remaining} more functions to reach 80%")
        if self.stats["coverage_percent"] < 90:
            print("   • Focus on core modules (domain/, services/) first")
        if self.stats["coverage_percent"] >= 80:
            print("   • Consider enabling --check-untyped-defs for core modules")

        print("=" * 60)


def main() -> None:
    """Main entry point."""
    analyzer = TypeCoverageAnalyzer()

    try:
        analyzer.analyze_package()
        analyzer.print_report()

        # Exit with appropriate code for CI/CD
        if analyzer.stats["coverage_percent"] < 70:
            sys.exit(1)  # Fail CI if coverage is too low
        elif analyzer.stats["coverage_percent"] < 80:
            sys.exit(2)  # Warning level
        else:
            sys.exit(0)  # Success

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
