from pathlib import Path
import os
import tempfile

def test_match():
    p = Path("app/models/user.py")
    patterns = ["**/models/**/*.py"]
    print(f"Path: {p}, Pattern: {patterns[0]}, Match: {p.match(patterns[0])}")

    p2 = Path("venv/lib/test.py")
    patterns2 = ["**/venv/**"]
    print(f"Path: {p2}, Pattern: {patterns2[0]}, Match: {p2.match(patterns2[0])}")

def test_resolve():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        resolved_base = base.resolve()
        print(f"Base: {base}")
        print(f"Resolved Base: {resolved_base}")
        
        file_path = base / "app" / "user.py"
        print(f"File Path: {file_path}")
        try:
            rel = file_path.relative_to(resolved_base)
            print(f"Relative (to resolved): {rel}")
        except ValueError as e:
            print(f"Relative (to resolved) Error: {e}")

if __name__ == "__main__":
    test_match()
    test_resolve()
