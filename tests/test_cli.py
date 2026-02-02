"""
Tests for the CLI interface.
"""

import argparse
from unittest.mock import MagicMock, patch

from alembic_autoscan.cli import check_command, main, scan_command
from alembic_autoscan.config import Config


class TestCLI:
    """Test suite for the CLI."""

    @patch("alembic_autoscan.cli.load_config")
    @patch("alembic_autoscan.cli.ModelScanner")
    @patch("alembic_autoscan.cli.get_project_root")
    def test_scan_command_basic(self, mock_get_root, mock_scanner_class, mock_load_config):
        """Test scan_command with default path."""
        mock_get_root.return_value = "/project/root"

        # Mock config
        mock_config = Config(
            base_path="/project/root", include_patterns=["*.py"], exclude_patterns=[]
        )
        mock_load_config.return_value = mock_config

        mock_scanner = MagicMock()
        mock_scanner.discover.return_value = ["model1", "model2"]
        mock_scanner_class.return_value = mock_scanner

        args = argparse.Namespace(
            path=None,
            include=None,
            exclude=None,
            verbose=False,
            no_cache=False,
            parallel=False,
            strict=False,
            config=None,
        )

        scan_command(args)

        mock_get_root.assert_called_once()
        mock_load_config.assert_called_once()
        mock_scanner_class.assert_called_once_with(
            base_path="/project/root",
            include_patterns=["*.py"],
            exclude_patterns=[],
            cache_enabled=True,
            parallel_enabled=None,
            parallel_threshold=100,
            strict_mode=False,
        )
        mock_scanner.discover.assert_called_once()

    @patch("alembic_autoscan.cli.load_config")
    @patch("alembic_autoscan.cli.ModelScanner")
    def test_scan_command_custom_path(self, mock_scanner_class, mock_load_config):
        """Test scan_command with custom path."""
        mock_config = Config(
            base_path="/custom/path",
            include_patterns=["**/models/**"],
            exclude_patterns=["**/tests/**"],
        )
        mock_load_config.return_value = mock_config

        mock_scanner = MagicMock()
        mock_scanner.discover.return_value = ["model1"]
        mock_scanner_class.return_value = mock_scanner

        args = argparse.Namespace(
            path="/custom/path",
            include=["**/models/**"],
            exclude=["**/tests/**"],
            verbose=False,
            no_cache=False,
            parallel=False,
            strict=False,
            config=None,
        )

        scan_command(args)

        mock_scanner_class.assert_called_once_with(
            base_path="/custom/path",
            include_patterns=["**/models/**"],
            exclude_patterns=["**/tests/**"],
            cache_enabled=True,
            parallel_enabled=None,
            parallel_threshold=100,
            strict_mode=False,
        )

    @patch("alembic_autoscan.cli.load_config")
    @patch("alembic_autoscan.cli.ModelScanner")
    def test_scan_command_no_models_found(self, mock_scanner_class, mock_load_config):
        """Test scan_command when no models are found."""
        mock_config = Config(base_path="/empty/path")
        mock_load_config.return_value = mock_config

        mock_scanner = MagicMock()
        mock_scanner.discover.return_value = []
        mock_scanner_class.return_value = mock_scanner

        args = argparse.Namespace(
            path="/empty/path",
            include=None,
            exclude=None,
            verbose=False,
            no_cache=False,
            parallel=False,
            strict=False,
            config=None,
        )

        with patch("builtins.print") as mock_print:
            scan_command(args)
            mock_print.assert_called_with("No SQLAlchemy models found in /empty/path")

    @patch("alembic_autoscan.cli.scan_command")
    def test_check_command_warning(self, mock_scan_command):
        """Test check_command prints warning and calls scan_command."""
        args = argparse.Namespace(path="/path")

        with patch("builtins.print") as mock_print:
            check_command(args)

            # Check if deprecation message was printed (at least once)
            calls = [call[0][0] for call in mock_print.call_args_list]
            assert any("DEPRECATED" in str(c) for c in calls)
            assert any("switching to the new `scan` command" in str(c) for c in calls)

        mock_scan_command.assert_called_once_with(args)

    @patch("argparse.ArgumentParser.parse_args")
    @patch("alembic_autoscan.cli.scan_command")
    def test_main_scan(self, mock_scan_command, mock_parse_args):
        """Test main entry point with scan command."""
        args = argparse.Namespace(command="scan")
        mock_parse_args.return_value = args

        main()

        mock_scan_command.assert_called_once_with(args)

    @patch("argparse.ArgumentParser.parse_args")
    @patch("alembic_autoscan.cli.scan_command")
    def test_main_discover(self, mock_scan_command, mock_parse_args):
        """Test main entry point with discover command (aliased to scan)."""
        args = argparse.Namespace(command="discover")
        mock_parse_args.return_value = args

        main()

        mock_scan_command.assert_called_once_with(args)

    @patch("argparse.ArgumentParser.parse_args")
    @patch("alembic_autoscan.cli.check_command")
    def test_main_check(self, mock_check_command, mock_parse_args):
        """Test main entry point with check command."""
        args = argparse.Namespace(command="check")
        mock_parse_args.return_value = args

        main()

        mock_check_command.assert_called_once_with(args)

    @patch("argparse.ArgumentParser.parse_args")
    @patch("argparse.ArgumentParser.print_help")
    def test_main_no_command(self, mock_print_help, mock_parse_args):
        """Test main entry point with no command."""
        args = argparse.Namespace(command=None)
        mock_parse_args.return_value = args

        main()

        mock_print_help.assert_called_once()
