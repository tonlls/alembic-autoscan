import tempfile
import time
from pathlib import Path

import pytest

from alembic_autoscan.scanner import ModelScanner


def create_nested_structure(base_dir: Path, depth: int, current_level: int, width: int):
    if current_level > depth:
        return

    # Create models in current directory
    for i in range(width):
        model_name = f"Model_L{current_level}_{i}"
        parent_name = f"Model_L{current_level - 1}_{i}" if current_level > 0 else "Base"

        content = f"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

# Complex imports to confuse simple parsers
from typing import (
    List,
    Optional,
    Union
)

{f"from ..model_{i} import {parent_name}" if current_level > 0 else "Base = declarative_base()"}

class {model_name}({parent_name}):
    __tablename__ = "table_l{current_level}_{i}"

    # Indented complex definition
    id = Column(
        Integer,
        primary_key=True,
        doc="The primary key"
    )

    def complex_method(self):
        if True:
            if True:
                return "nested"
"""
        (base_dir / f"model_{i}.py").write_text(content)

    # Recurse
    if current_level < depth:
        for w in range(width):
            subdir = base_dir / f"sub_{w}"
            subdir.mkdir()
            create_nested_structure(subdir, depth, current_level + 1, width)


def test_complex_nested_structure_performance():
    """
    Stress test with deep directory nesting, inheritance chains, and complex code indentation.
    Designed to be computationally expensive for the scanner.
    """
    # Configuration for "Heavy" load
    # Depth 5, Width 3 -> 1 + 3 + 9 + 27 + 81 + 243 directories
    # Actually just simple recursion:
    # At each level we create 'width' subdirectories.
    # Total directories = roughly width^depth
    # With depth=5, width=3, we get too many files potentially.
    # let's do depth=4, width=3.
    # - Root
    #   - sub_0 (recursive)
    #   - sub_1
    #   - sub_2
    # files per dir = 3.
    # Total nodes in tree (dirs) = (3^(4+1) - 1) / (3-1) = (243-1)/2 = 121 dirs.
    # Total files = 121 * 3 = 363 files.
    # This is substantial but safe.

    DEPTH = 4
    WIDTH = 3
    FILES_PER_DIR = 3

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)

        print(f"\nGenerating complex structure (Depth={DEPTH}, Width={WIDTH})...")
        gen_start = time.perf_counter()
        create_nested_structure(base_path, DEPTH, 0, FILES_PER_DIR)
        gen_time = time.perf_counter() - gen_start
        print(f"Generation took {gen_time:.4f}s")

        # Cold Scan
        print("Starting Cold Scan...")
        start_cold = time.perf_counter()
        scanner = ModelScanner(base_path=str(base_path), cache_enabled=True)
        discovered = scanner.discover()
        cold_time = time.perf_counter() - start_cold

        print(f"Cold Scan took {cold_time:.4f}s")
        print(f"Discovered {len(discovered)} models")

        # Warm Scan
        print("Starting Warm Scan...")
        start_warm = time.perf_counter()
        scanner2 = ModelScanner(base_path=str(base_path), cache_enabled=True)
        discovered2 = scanner2.discover()
        warm_time = time.perf_counter() - start_warm

        print(f"Warm Scan took {warm_time:.4f}s")

        assert len(discovered) > 100
        assert len(discovered) == len(discovered2)
        assert warm_time < cold_time

        # Performance degradation check (soft assertion)
        # Verify that it didn't take *too* long (e.g. < 5 seconds for ~400 files)
        # If it takes too long, the algorithm might be inefficient.
        assert cold_time < 10.0, "Cold scan took dangerously long (>10s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
