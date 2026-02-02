"""
Model scanner for discovering SQLAlchemy models in a codebase.
"""

import ast
import importlib
import importlib.util
import logging
import sys
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count
from pathlib import Path
from typing import List, Optional, Set, Tuple

from .cache import ScanCache
from .utils import parse_gitignore

logger = logging.getLogger(__name__)


# --- AST Helper Functions (Standalone for Parallelization) ---


def _is_sqlmodel(node: ast.ClassDef) -> bool:
    """Check if a class is a SQLModel with table=True."""
    if not node.bases:
        return False

    # Check if this class inherits from SQLModel
    has_sqlmodel_base = False
    for base in node.bases:
        # Check for SQLModel base class
        if isinstance(base, ast.Name) and base.id == "SQLModel":
            has_sqlmodel_base = True

        # Check for SQLModel(..., table=True)
        if isinstance(base, ast.Call):
            if isinstance(base.func, ast.Name) and base.func.id == "SQLModel":
                # Check for table=True keyword argument
                for keyword in base.keywords:
                    if keyword.arg == "table" and isinstance(keyword.value, ast.Constant):
                        if keyword.value.value is True:
                            return True

    # For class Hero(SQLModel, table=True), the table=True appears
    # as a keyword in the class definition
    if has_sqlmodel_base:
        for keyword in node.keywords:
            if keyword.arg == "table" and isinstance(keyword.value, ast.Constant):
                if keyword.value.value is True:
                    return True

    return False


def _is_abstract_class(node: ast.ClassDef) -> bool:
    """Check if a class is marked as abstract."""
    for item in node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name) and target.id == "__abstract__":
                    # Check if the value is True
                    if isinstance(item.value, ast.Constant):
                        if item.value.value is True:
                            return True
    return False


def _is_column_call(node: Optional[ast.AST]) -> bool:
    """Check if an AST node is a call to Column() or mapped_column()."""
    if not isinstance(node, ast.Call):
        return False

    func = node.func
    if isinstance(func, ast.Name):
        return func.id in ["Column", "mapped_column"]
    elif isinstance(func, ast.Attribute):
        return func.attr in ["Column", "mapped_column"]

    return False


def _is_sqlalchemy_model(node: ast.ClassDef) -> bool:
    """Check if an AST class node represents a SQLAlchemy model."""
    # Check for SQLModel with table=True
    if _is_sqlmodel(node):
        return True

    # Check decorators
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name):
            if decorator.id in ["as_declarative", "declarative_base"]:
                return True
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                if decorator.func.id in ["as_declarative", "declarative_base"]:
                    return True
            elif isinstance(decorator.func, ast.Attribute):
                if decorator.func.attr in ["as_declarative", "declarative_base"]:
                    return True

    if not node.bases:
        return False

    for base in node.bases:
        # Direct inheritance: class User(Base)
        if isinstance(base, ast.Name):
            base_name = base.id
            if base_name in ["Base", "DeclarativeBase", "Model"] or base_name.endswith("Base"):
                return True

        # Attribute access: class User(db.Model)
        elif isinstance(base, ast.Attribute):
            if base.attr in ["Model", "DeclarativeBase"] or base.attr.endswith("Base"):
                return True

        # Function call: class User(declarative_base())
        elif isinstance(base, ast.Call):
            if isinstance(base.func, ast.Name):
                if base.func.id == "declarative_base":
                    return True

    return False


def _has_table_definition(node: ast.ClassDef) -> bool:
    """Check if a class has SQLAlchemy table indicators."""
    if _is_sqlmodel(node):
        return True

    for item in node.body:
        # Check for __tablename__ or __table__
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    if target.id in ["__tablename__", "__table__"]:
                        return True

        # Check for Column definitions or Mapped annotations
        if isinstance(item, ast.AnnAssign):
            # Check for Mapped[int]
            if isinstance(item.annotation, ast.Subscript):
                if isinstance(item.annotation.value, ast.Name):
                    if item.annotation.value.id == "Mapped":
                        return True

            # Check for mapped_column() or Column() in the value
            value = getattr(item, "value", None)
            if value is not None and _is_column_call(value):
                return True

        if isinstance(item, ast.Assign):
            if _is_column_call(item.value):
                return True

    return False


def _has_tablename(node: ast.ClassDef) -> bool:
    """Check if a class has __tablename__ defined."""
    for item in node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name) and target.id == "__tablename__":
                    return True
    return False


def scan_file_worker(file_path: Path) -> Tuple[Path, bool, List[str]]:
    """
    Scan a Python file for SQLAlchemy models using AST.

    Returns:
        Tuple of (file_path, is_model, list_of_abstract_classes)
    """
    abstract_classes = []
    has_concrete_model = False

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))

        # Look for class definitions and imperative mapping calls
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's abstract first
                if _is_abstract_class(node):
                    abstract_classes.append(node.name)
                    continue  # Skip abstract classes

                # Check if it's a SQLAlchemy model
                is_model = _is_sqlalchemy_model(node)
                has_table = _has_table_definition(node)

                if _has_tablename(node):
                    has_concrete_model = True
                elif _is_sqlmodel(node):
                    has_concrete_model = True
                elif is_model and has_table:
                    has_concrete_model = True

            # Check for imperative mapping
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute):
                    if func.attr == "map_imperatively":
                        has_concrete_model = True
                elif isinstance(func, ast.Name):
                    if func.id == "map_imperatively":
                        has_concrete_model = True

        return file_path, has_concrete_model, abstract_classes

    except (SyntaxError, UnicodeDecodeError, OSError):
        # Skip files that can't be parsed or read
        return file_path, False, []
    except Exception as e:
        logger.debug(f"Error scanning {file_path}: {e}")
        return file_path, False, []


class ModelScanner:
    """
    Scans Python files to discover SQLAlchemy model classes using AST parsing.
    """

    DEFAULT_EXCLUDE_PATTERNS = [
        "**/venv/**",
        "**/env/**",
        "**/.venv/**",
        "**/my_venv/**",
        "**/site-packages/**",
        "**/tests/**",
        "**/test/**",
        "**/migrations/**",
        "**/alembic/**",
        "**/__pycache__/**",
        "**/.git/**",
        "**/.idea/**",
        "**/.vscode/**",
        "**/node_modules/**",
        "**/build/**",
        "**/dist/**",
    ]

    def __init__(
        self,
        base_path: str = ".",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        cache_enabled: bool = True,
        parallel_enabled: Optional[bool] = None,
        parallel_threshold: int = 50,
        strict_mode: bool = False,
    ):
        """
        Initialize the ModelScanner.

        Args:
            base_path: Root directory to start scanning from
            include_patterns: Glob patterns for files to include
            exclude_patterns: Glob patterns for files to exclude
            cache_enabled: Whether to enable caching of scan results
            parallel_enabled: Whether to enable parallel scanning (None=auto)
            parallel_threshold: Minimum files for parallel scanning
            strict_mode: If True, verify imports during discovery
        """
        self.base_path = Path(base_path).resolve()
        self.include_patterns = include_patterns or ["**/*.py"]
        self.exclude_patterns = (exclude_patterns or []) + self.DEFAULT_EXCLUDE_PATTERNS
        self.cache_enabled = cache_enabled
        self.parallel_enabled = parallel_enabled
        self.parallel_threshold = parallel_threshold
        self.strict_mode = strict_mode
        self._discovered_modules: Set[str] = set()
        self._abstract_classes: Set[str] = set()

        # Initialize cache
        self.cache = ScanCache(cache_dir=self.base_path, enabled=cache_enabled)

        # Load gitignore patterns
        gitignore_path = self.base_path / ".gitignore"
        gitignore_patterns = parse_gitignore(gitignore_path)
        if gitignore_patterns:
            self.exclude_patterns.extend(gitignore_patterns)

    def _matches_pattern(self, path: Path, patterns: List[str]) -> bool:
        """Check if a path matches any of the given glob patterns."""
        try:
            if not path.is_absolute():
                path_to_match = path
            else:
                path_to_match = path.relative_to(self.base_path)
        except (ValueError, OSError):
            path_to_match = path

        for pattern in patterns:
            if path_to_match.match(pattern):
                return True

            # Additional matching heuristics for recursive patterns
            if pattern.startswith("**/"):
                simplified = pattern[3:]
                if path_to_match.match(simplified):
                    return True

            if pattern.startswith("**/") and pattern.endswith("/**"):
                middle = pattern[3:-3]
                if middle in path_to_match.parts:
                    alt_pattern = pattern[3:]
                    if path_to_match.match(alt_pattern) or path_to_match.match(alt_pattern + "/*"):
                        return True

            if "/**/" in pattern:
                simplified_pattern = pattern.replace("/**/", "/")
                if path_to_match.match(simplified_pattern):
                    return True

            if pattern.endswith("/**"):
                if path_to_match.match(pattern + "/*"):
                    return True

        return False

    def _should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned based on include/exclude patterns."""
        if not self._matches_pattern(file_path, self.include_patterns):
            return False
        if self._matches_pattern(file_path, self.exclude_patterns):
            return False
        return True

    def _get_module_path(self, file_path: Path) -> Optional[str]:
        """Convert a file path to a Python module path."""
        try:
            abs_file_path = file_path.resolve()
            rel_path = abs_file_path.relative_to(self.base_path)
            if rel_path.suffix == ".py":
                rel_path = rel_path.with_suffix("")

            parts = list(rel_path.parts)
            if parts[-1] == "__init__":
                parts = parts[:-1]

            if not parts:
                return None

            return ".".join(parts)
        except ValueError:
            return None

    def discover(self) -> List[str]:
        """
        Discover all SQLAlchemy model modules in the codebase.

        Returns:
            List of module paths
        """
        self._discovered_modules.clear()
        self._abstract_classes.clear()

        # Step 1: Collect all files to scan
        files_to_check = []
        for file_path in self.base_path.rglob("*.py"):
            if self._should_scan_file(file_path):
                files_to_check.append(file_path)

        # Step 2: Load cache
        cache_data = (
            self.cache.load(str(self.base_path), self.include_patterns, self.exclude_patterns) or {}
        )

        # Step 3: Determine which files need scanning vs can be served from cache
        files_to_scan = []
        new_cache_data = {}  # Store updated cache info

        for file_path in files_to_check:
            path_str = str(file_path.resolve())

            # Check if file needs rescanning
            needs_rescan = True
            if path_str in cache_data:
                mtime, is_model, module_path = cache_data[path_str]
                if not self.cache.is_file_modified(file_path, mtime):
                    needs_rescan = False
                    # Use cached result
                    if is_model:
                        new_cache_data[path_str] = (mtime, True, module_path)
                        if module_path:
                            self._discovered_modules.add(module_path)
                    else:
                        new_cache_data[path_str] = (mtime, False, None)

            if needs_rescan:
                files_to_scan.append(file_path)

        # Step 4: Scan remaining files
        if files_to_scan:
            logger.info(f"Scanning {len(files_to_scan)} files...")

            results = []

            # Determine if we should use parallel processing
            should_parallel = self.parallel_enabled
            if should_parallel is None:
                should_parallel = len(files_to_scan) >= self.parallel_threshold

            if should_parallel and len(files_to_scan) > 1:
                max_workers = min(len(files_to_scan), cpu_count() or 1)
                try:
                    with ProcessPoolExecutor(max_workers=max_workers) as executor:
                        results = list(executor.map(scan_file_worker, files_to_scan))
                except Exception as e:
                    logger.warning(f"Parallel scanning failed, falling back to serial: {e}")
                    results = [scan_file_worker(f) for f in files_to_scan]
            else:
                results = [scan_file_worker(f) for f in files_to_scan]

            # Collect results
            for file_path, is_model, abstracts in results:
                path_str = str(file_path.resolve())
                module_path = self._get_module_path(file_path)
                mtime = file_path.stat().st_mtime

                self._abstract_classes.update(abstracts)

                if is_model and module_path:
                    self._discovered_modules.add(module_path)
                    new_cache_data[path_str] = (mtime, True, module_path)
                else:
                    new_cache_data[path_str] = (mtime, False, module_path)

        # Step 5: Save cache
        self.cache.save(
            str(self.base_path), self.include_patterns, self.exclude_patterns, new_cache_data
        )

        discovered = sorted(self._discovered_modules)

        # Step 6: Strict mode verification
        if self.strict_mode:
            self.verify_imports(discovered)

        return discovered

    def verify_imports(self, modules: List[str]) -> List[str]:
        """
        Verify that modules are importable.

        Returns:
            List of successfully imported modules
        """
        verified = []
        base_path_str = str(self.base_path)
        if base_path_str not in sys.path:
            sys.path.insert(0, base_path_str)

        for module in modules:
            try:
                importlib.import_module(module)
                verified.append(module)
            except Exception as e:
                logger.error(f"Failed to verify module {module}: {e}")
                # We don't remove it from the list, just log it,
                # as the user might want to know it exists but is broken
        return verified

    def import_models(self, modules: Optional[List[str]] = None) -> int:
        """Import discovered model modules."""
        if modules is None:
            modules = list(self._discovered_modules)

        imported_count = 0
        base_path_str = str(self.base_path)
        if base_path_str not in sys.path:
            sys.path.insert(0, base_path_str)

        for module_path in modules:
            try:
                importlib.import_module(module_path)
                imported_count += 1
            except ImportError as e:
                print(f"Warning: Could not import {module_path}: {e}", file=sys.stderr)
                continue

        return imported_count
