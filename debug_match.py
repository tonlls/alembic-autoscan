from pathlib import Path
import fnmatch

def test_match():
    cases = [
        ("app/models/user.py", "**/*.py"),
        ("venv/lib/test.py", "**/venv/**"),
        ("tests/test_foo.py", "**/tests/**"),
        ("app/tests/test_bar.py", "**/tests/**"),
    ]
    
    for p_str, pat in cases:
        p = Path(p_str)
        match_path = p.match(pat)
        match_fn = fnmatch.fnmatch(p_str, pat)
        # also try fnmatch with a leading slash or something?
        print(f"Path: {p_str:25} | Pattern: {pat:15} | Path.match: {match_path:5} | fnmatch: {match_fn:5}")

if __name__ == "__main__":
    test_match()
