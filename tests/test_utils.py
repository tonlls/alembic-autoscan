from pathlib import Path
from unittest.mock import mock_open, patch

from alembic_autoscan.utils import parse_gitignore


def test_parse_gitignore_negation(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("!negated.txt\nnormal.txt")

    patterns = parse_gitignore(gitignore)
    # The negation should be skipped (line 38 hit)
    assert "**/normal.txt/**" in patterns or "**/normal.txt" in patterns
    # Verify exact outputs if possible, but the key is we hit the continue
    # Based on code: normal.txt -> patterns.append("**/" + pattern + "/**") and "**/" + pattern
    # It appends both for simple names.

    # We just want to make sure it runs without error and negations are ignored.
    assert not any("negated.txt" in p and "!" in p for p in patterns)


def test_parse_gitignore_root_anchored(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("/root_dir\n/root_file.txt")

    patterns = parse_gitignore(gitignore)
    # Line 47 hit
    # /root_dir -> root_dir
    # Code logic: if startswith("/") -> pattern = pattern[1:]
    # Then it continues. matches "node_modules" branch logic? No, check logic flow.
    # Logic in utils.py:
    # ...
    # if pattern.startswith("/"):
    #     pattern = pattern[1:]
    # else:
    #     ... (complex logic)
    #
    # Wait, if it goes into `if pattern.startswith("/"):`, it effectively strips it.
    # Then it falls through to `patterns.append(pattern)` at the end of the loop?
    # Let's check the code content from previous turn.

    # Line 45: if pattern.startswith("/"):
    # Line 47:    pattern = pattern[1:]
    # Line 48: else:
    # ...
    # Line 63: patterns.append(pattern)

    # So if it was /root_dir, it becomes root_dir.
    assert "root_dir" in patterns
    assert "root_file.txt" in patterns


def test_parse_gitignore_oserror():
    # Mock open to raise OSError
    with patch("builtins.open", mock_open()) as mocked_file:
        mocked_file.side_effect = OSError("Access denied")

        # We need a path that exists for existing check, but open fails
        with patch.object(Path, "exists", return_value=True):
            patterns = parse_gitignore(Path("dummy"))
            assert patterns == []
