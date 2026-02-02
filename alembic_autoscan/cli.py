import argparse
import sys

from .config import load_config, setup_logging
from .integration import get_project_root
from .scanner import ModelScanner


def scan_command(args: argparse.Namespace) -> None:
    """Handle the 'scan' (formerly 'discover') command."""
    path = args.path
    if not path:
        # If no path provided, try to find project root or use current dir
        path = str(get_project_root())

    # Load configuration
    config = load_config(
        base_path=path,
        include_patterns=args.include,
        exclude_patterns=args.exclude,
        log_level="DEBUG" if args.verbose else None,
        cache_enabled=False if args.no_cache else None,
        parallel_enabled=True if args.parallel else None,
        strict_mode=True if args.strict else None,
        config_file=args.config,
    )

    setup_logging(config.log_level)

    scanner = ModelScanner(
        base_path=config.base_path,
        include_patterns=config.include_patterns,
        exclude_patterns=config.exclude_patterns,
        cache_enabled=config.cache_enabled,
        parallel_enabled=config.parallel_enabled,
        parallel_threshold=config.parallel_threshold,
        strict_mode=config.strict_mode,
    )

    modules = scanner.discover()

    if not modules:
        print(f"No SQLAlchemy models found in {config.base_path}")
        return

    print(f"Discovered {len(modules)} model modules in {config.base_path}:")
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
        subparser.add_argument(
            "--no-cache",
            action="store_true",
            help="Disable caching of scan results",
        )
        subparser.add_argument(
            "--parallel",
            action="store_true",
            help="Force parallel scanning",
        )
        subparser.add_argument(
            "--strict",
            action="store_true",
            help="Verify that models can be imported",
        )
        subparser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Enable verbose logging",
        )
        subparser.add_argument(
            "-c",
            "--config",
            help="Path to configuration file",
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
