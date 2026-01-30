import sys
from pathlib import Path
from alembic_autoscan.scanner import ModelScanner

def test_discovery():
    base_path = Path("examples/edge_cases").resolve()
    scanner = ModelScanner(base_path=str(base_path))
    modules = scanner.discover()
    
    print("Discovered modules:")
    for module in modules:
        print(f"  - {module}")

if __name__ == "__main__":
    test_discovery()
