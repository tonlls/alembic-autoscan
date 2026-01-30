"""
CLI interface for alembic-autoscan.
"""

import argparse
import sys
import os
from typing import List, Optional

from .scanner import ModelScanner
from .integration import get_project_root


def discover_command(args: argparse.Namespace) -> None:
    """Handle the 'discover' command."""
    path = args.path
    if not path:
        # If no path provided, try to find project root or use current dir
        path = str(get_project_root())

    scanner = ModelScanner(
        base_path=path,
        include_patterns=args.include,
        exclude_patterns=args.exclude,
    )

    modules = scanner.discover()

    if not modules:
        print(f"No SQLAlchemy models found in {path}")
        return

    print(f"Discovered {len(modules)} model modules in {path}:")
    for module in modules:
        print(f"  - {module}")


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Automatically discover SQLAlchemy models for Alembic."
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Discover command
    discover_parser = subparsers.add_parser(
        "discover", help="Scan a directory for SQLAlchemy models"
    )
    discover_parser.add_argument(
        "path",
        nargs="?",
        help="Path to scan (defaults to project root or current directory)",
    )
    discover_parser.add_argument(
        "-i",
        "--include",
        action="append",
        help="Glob patterns to include (e.g., '**/models/**')",
    )
    discover_parser.add_argument(
        "-e",
        "--exclude",
        action="append",
        help="Glob patterns to exclude (e.g., '**/tests/**')",
    )

    args = parser.parse_args()

    if args.command == "discover":
        discover_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
