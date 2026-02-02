import json
import tempfile
import time
from pathlib import Path

import pytest

from alembic_autoscan.scanner import ModelScanner


def test_large_scale_scanning_with_cache():
    """Test scanning a large number of models with caching enabled."""
    num_models = 50  # Enough to demonstrate "a lot" without being too slow

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        models_dir = base_path / "models"
        models_dir.mkdir()

        # Create a large number of model files
        for i in range(num_models):
            model_file = models_dir / f"model_{i}.py"
            model_file.write_text(
                f"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Model{i}(Base):
    __tablename__ = "table_{i}"
    id = Column(Integer, primary_key=True)
    name = Column(String)
"""
            )

        # First scan - should populate cache
        start_time = time.time()
        scanner = ModelScanner(base_path=str(base_path), cache_enabled=True)
        discovered = scanner.discover()
        first_scan_time = time.time() - start_time

        assert len(discovered) == num_models
        for i in range(num_models):
            assert f"models.model_{i}" in discovered

        # Verify cache file was created
        cache_file = base_path / ".alembic-autoscan.cache"
        assert cache_file.exists()

        # Verify cache content structure
        with cache_file.open() as f:
            cache_data = json.load(f)
            # There should be at least one key (the hash)
            assert len(cache_data) > 0
            # Inspect the first key
            cache_key = list(cache_data.keys())[0]
            entries = cache_data[cache_key]
            # Should have entries for all our files
            assert len(entries) >= num_models

        # Second scan - should use cache
        # We re-instantiate to ensure it loads from disk
        start_time = time.time()
        scanner2 = ModelScanner(base_path=str(base_path), cache_enabled=True)
        discovered2 = scanner2.discover()
        second_scan_time = time.time() - start_time

        assert len(discovered2) == num_models
        assert discovered == discovered2

        # While performance tests are tricky in CI, the second scan should be generally fast
        # We won't assert on time difference to avoid flakiness, but the logic holds.

        print(f"\nFirst scan time: {first_scan_time:.4f}s")
        print(f"Second scan time: {second_scan_time:.4f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


def test_performance_improvement():
    """
    Performance test to verify that caching actually improves scan speed.
    This creates a larger dataset to make the timing difference measurable.
    Also compares against running with cache completely disabled.
    """
    num_models = 100  # More models for better timing data

    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        models_dir = base_path / "models"
        models_dir.mkdir()

        # Generate models
        for i in range(num_models):
            (models_dir / f"perf_model_{i}.py").write_text(
                f"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PerfModel{i}(Base):
    __tablename__ = "perf_table_{i}"
    id = Column(Integer, primary_key=True)
"""
            )

        # 1. No Cache (Baseline)
        start_no_cache = time.perf_counter()
        scanner_no_cache = ModelScanner(base_path=str(base_path), cache_enabled=False)
        scanner_no_cache.discover()
        duration_no_cache = time.perf_counter() - start_no_cache

        # 2. Cold Scan (Cache Enabled but empty)
        # We use a new scanner instance for each run to be fair
        start_cold = time.perf_counter()
        scanner1 = ModelScanner(base_path=str(base_path), cache_enabled=True)
        scanner1.discover()
        duration_cold = time.perf_counter() - start_cold

        # 3. Warm Scan (Cache Enabled and populated)
        start_warm = time.perf_counter()
        scanner2 = ModelScanner(base_path=str(base_path), cache_enabled=True)
        scanner2.discover()
        duration_warm = time.perf_counter() - start_warm

        print(f"\nPerformance Result (N={num_models}):")
        print(f"No Cache:  {duration_no_cache:.6f}s")
        print(f"Cold scan: {duration_cold:.6f}s")
        print(f"Warm scan: {duration_warm:.6f}s")

        # Avoid division by zero
        if duration_warm > 0:
            print(f"Speedup vs Cold: {duration_cold / duration_warm:.2f}x")
            print(f"Speedup vs No Cache: {duration_no_cache / duration_warm:.2f}x")

        # Assert that using the cache is faster
        # Note: On extremely fast creates/scans or busy systems, this could theoretically flake,
        # but with 100 files parsing vs reading a single JSON, it should be robust.
        assert duration_warm < duration_cold, "Cached scan should be faster than cold scan"
        assert duration_warm < duration_no_cache, "Cached scan should be faster than no cache"
