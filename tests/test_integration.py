"""
Tests for the integration helpers.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from alembic_autoscan.integration import (
    get_project_root,
    import_models,
    import_models_from_project_root,
)


class TestIntegration:
    """Test suite for integration helpers."""

    @patch("alembic_autoscan.integration.ModelScanner")
    def test_import_models_basic(self, mock_scanner_class):
        """Test import_models with default arguments."""
        mock_scanner = MagicMock()
        mock_scanner.discover.return_value = ["app.models.user"]
        mock_scanner.import_models.return_value = 1
        mock_scanner_class.return_value = mock_scanner

        count = import_models()

        assert count == 1
        mock_scanner_class.assert_called_once()
        mock_scanner.discover.assert_called_once()
        mock_scanner.import_models.assert_called_with(["app.models.user"])

    @patch("alembic_autoscan.integration.ModelScanner")
    def test_import_models_custom(self, mock_scanner_class):
        """Test import_models with custom arguments."""
        mock_scanner = MagicMock()
        mock_scanner.discover.return_value = ["app.models.user"]
        mock_scanner.import_models.return_value = 1
        mock_scanner_class.return_value = mock_scanner

        count = import_models(
            base_path="/tmp/test",
            include_patterns=["**/models/**"],
            exclude_patterns=["**/tests/**"],
            verbose=True,
        )

        assert count == 1
        mock_scanner_class.assert_called_once_with(
            base_path="/tmp/test",
            include_patterns=["**/models/**"],
            exclude_patterns=["**/tests/**"],
        )

    def test_get_project_root(self, tmp_path):
        """Test get_project_root finding markers."""
        # Create a mock project structure
        project_root = tmp_path / "my_project"
        project_root.mkdir()
        (project_root / "pyproject.toml").touch()

        sub_dir = project_root / "src" / "myapp"
        sub_dir.mkdir(parents=True)

        # Change CWD to sub_dir
        with patch("pathlib.Path.cwd", return_value=sub_dir):
            root = get_project_root()
            assert root == project_root

    def test_get_project_root_no_marker(self, tmp_path):
        """Test get_project_root when no marker is found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with patch("pathlib.Path.cwd", return_value=empty_dir):
            # It should return current directory if no marker found in parents
            root = get_project_root()
            assert root == empty_dir

    @patch("alembic_autoscan.integration.get_project_root")
    @patch("alembic_autoscan.integration.import_models")
    def test_import_models_from_project_root(self, mock_import_models, mock_get_root):
        """Test import_models_from_project_root."""
        mock_get_root.return_value = Path("/project/root")
        mock_import_models.return_value = 5

        count = import_models_from_project_root(verbose=True)

        assert count == 5
        mock_get_root.assert_called_once()
        mock_import_models.assert_called_once_with(
            base_path="/project/root", include_patterns=None, exclude_patterns=None, verbose=True
        )
