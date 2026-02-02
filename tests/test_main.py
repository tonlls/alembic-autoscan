import runpy
import sys
from unittest.mock import patch

import pytest


def test_main_module_invocation():
    # Mock sys.argv to avoid actually doing anything
    # We use --version or --help to exit quickly
    with patch.object(sys, "argv", ["alembic-autoscan", "--version"]):
        with pytest.raises(SystemExit):
            runpy.run_module("alembic_autoscan", run_name="__main__")
