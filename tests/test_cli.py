"""
Tests for the CLI interface.
"""

import argparse
from unittest.mock import MagicMock, patch

from alembic_autoscan.cli import discover_command, main


class TestCLI:
    """Test suite for the CLI."""

    @patch("alembic_autoscan.cli.ModelScanner")
    @patch("alembic_autoscan.cli.get_project_root")
    def test_discover_command_basic(self, mock_get_root, mock_scanner_class):
        """Test discover_command with default path."""
        mock_get_root.return_value = "/project/root"
        mock_scanner = MagicMock()
        mock_scanner.discover.return_value = ["model1", "model2"]
        mock_scanner_class.return_value = mock_scanner

        args = argparse.Namespace(path=None, include=None, exclude=None)

        discover_command(args)

        mock_get_root.assert_called_once()
        mock_scanner_class.assert_called_once_with(
            base_path="/project/root", include_patterns=None, exclude_patterns=None
        )
        mock_scanner.discover.assert_called_once()

    @patch("alembic_autoscan.cli.ModelScanner")
    def test_discover_command_custom_path(self, mock_scanner_class):
        """Test discover_command with custom path."""
        mock_scanner = MagicMock()
        mock_scanner.discover.return_value = ["model1"]
        mock_scanner_class.return_value = mock_scanner

        args = argparse.Namespace(
            path="/custom/path", include=["**/models/**"], exclude=["**/tests/**"]
        )

        discover_command(args)

        mock_scanner_class.assert_called_once_with(
            base_path="/custom/path",
            include_patterns=["**/models/**"],
            exclude_patterns=["**/tests/**"],
        )

    @patch("alembic_autoscan.cli.ModelScanner")
    def test_discover_command_no_models_found(self, mock_scanner_class):
        """Test discover_command when no models are found."""
        mock_scanner = MagicMock()
        mock_scanner.discover.return_value = []
        mock_scanner_class.return_value = mock_scanner

        args = argparse.Namespace(path="/empty/path", include=None, exclude=None)

        with patch("builtins.print") as mock_print:
            discover_command(args)
            mock_print.assert_called_with("No SQLAlchemy models found in /empty/path")

    @patch("argparse.ArgumentParser.parse_args")
    @patch("alembic_autoscan.cli.discover_command")
    def test_main_discover(self, mock_discover_command, mock_parse_args):
        """Test main entry point with discover command."""
        args = argparse.Namespace(command="discover")
        mock_parse_args.return_value = args

        main()

        mock_discover_command.assert_called_once_with(args)

    @patch("argparse.ArgumentParser.parse_args")
    @patch("argparse.ArgumentParser.print_help")
    def test_main_no_command(self, mock_print_help, mock_parse_args):
        """Test main entry point with no command."""
        args = argparse.Namespace(command=None)
        mock_parse_args.return_value = args

        main()

        mock_print_help.assert_called_once()
