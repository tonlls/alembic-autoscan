import argparse
import sys

from .integration import get_project_root
from .scanner import ModelScanner


def scan_command(args: argparse.Namespace) -> None:
    """Handle the 'scan' (formerly 'discover') command."""
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


# Alias for backward compatibility
discover_command = scan_command


def check_command(args: argparse.Namespace) -> None:
    """Handle the deprecated 'check' command."""
    print(
        "DEPRECATED: this command (`check`) has been DEPRECATED, "
        "and will be unsupported beyond 01 June 2024.",
        file=sys.stderr,
    )
    print(
        "We highly encourage switching to the new `scan` command which is easier to use, "
        "more powerful, and can be set up to mimic the deprecated command if required.",
        file=sys.stderr,
    )
    print("", file=sys.stderr)
    scan_command(args)


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Automatically discover SQLAlchemy models for Alembic."
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Common arguments for scan-like commands
    def add_scan_args(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument(
            "path",
            nargs="?",
            help="Path to scan (defaults to project root or current directory)",
        )
        subparser.add_argument(
            "-i",
            "--include",
            action="append",
            help="Glob patterns to include (e.g., '**/models/**')",
        )
        subparser.add_argument(
            "-e",
            "--exclude",
            action="append",
            help="Glob patterns to exclude (e.g., '**/tests/**')",
        )

    # Scan command (new primary command)
    scan_parser = subparsers.add_parser("scan", help="Scan a directory for SQLAlchemy models")
    add_scan_args(scan_parser)

    # Discover command (old name, kept for compatibility)
    discover_parser = subparsers.add_parser(
        "discover", help="Scan a directory for SQLAlchemy models (aliased to 'scan')"
    )
    add_scan_args(discover_parser)

    # Check command (deprecated)
    check_parser = subparsers.add_parser("check", help="[DEPRECATED] Use 'scan' instead")
    add_scan_args(check_parser)

    args = parser.parse_args()

    if args.command in ["scan", "discover"]:
        scan_command(args)
    elif args.command == "check":
        check_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
