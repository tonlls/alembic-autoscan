"""
Model scanner for discovering SQLAlchemy models in a codebase.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Set, Optional
import importlib.util
import fnmatch



class ModelScanner:
    """
    Scans Python files to discover SQLAlchemy model classes using AST parsing.
    """

    DEFAULT_EXCLUDE_PATTERNS = [
        "**/venv/**",
        "**/env/**",
        "**/.venv/**",
        "**/site-packages/**",
        "**/tests/**",
        "**/test/**",
        "**/migrations/**",
        "**/alembic/**",
    ]

    def __init__(
        self,
        base_path: str = ".",
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ):
        """
        Initialize the ModelScanner.

        Args:
            base_path: Root directory to start scanning from
            include_patterns: Glob patterns for files to include (default: ["**/*.py"])
            exclude_patterns: Glob patterns for files to exclude
        """
        self.base_path = Path(base_path).resolve()
        self.include_patterns = include_patterns or ["**/*.py"]
        self.exclude_patterns = (exclude_patterns or []) + self.DEFAULT_EXCLUDE_PATTERNS
        self._discovered_modules: Set[str] = set()

    def _matches_pattern(self, path: Path, patterns: List[str]) -> bool:
        """Check if a path matches any of the given glob patterns."""
        # Convert to PurePath for consistent matching behavior
        # Use the path as-is if it's relative, otherwise try to make it relative to base_path
        try:
            if not path.is_absolute():
                # Path is already relative, use it directly
                path_to_match = path
            else:
                # Try to make it relative to base_path
                path_to_match = path.relative_to(self.base_path)
        except (ValueError, OSError):
            # If we can't make it relative, use the original path
            path_to_match = path

        for pattern in patterns:
            # Try the pattern as-is first
            if path_to_match.match(pattern):
                return True
            
            # Handle patterns like **/segment/** which should match any file under 'segment' directory
            # Path.match() has a quirk where **/venv/**/* won't match venv/lib/test.py
            # because ** at the start requires at least one component before 'venv'
            # So we also try without the leading **
            if pattern.startswith('**/') and pattern.endswith('/**'):
                # Extract the middle segment(s)
                # E.g., **/venv/** -> venv
                middle = pattern[3:-3]  # Remove **/ from start and /** from end
                
                # Check if this segment appears in the path parts
                if middle in path_to_match.parts:
                    # Now check if the file is actually under this directory
                    # Try the pattern without the leading **/ 
                    alt_pattern = pattern[3:]  # Remove **/ from start -> venv/**
                    # First try without adding anything (matches files directly in the directory)
                    if path_to_match.match(alt_pattern):
                        return True
                    # Also try with /* appended (matches files in subdirectories)
                    if path_to_match.match(alt_pattern + '/*'):
                        return True
            
            # Handle patterns with /** in the middle like **/models/**/*.py
            # These should match both files in subdirectories AND files directly in the directory
            # E.g., **/models/**/*.py should match both app/models/user.py and app/models/sub/user.py
            if '/**/' in pattern:
                # Try replacing /** with / to match files directly in the directory
                simplified_pattern = pattern.replace('/**/', '/')
                if path_to_match.match(simplified_pattern):
                    return True
            
            # Also try appending /* to patterns ending with /** 
            # to match files directly under matching directories
            if pattern.endswith('/**'):
                if path_to_match.match(pattern + '/*'):
                    return True
        
        return False

    def _should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned based on include/exclude patterns."""
        # Check if file matches include patterns
        if not self._matches_pattern(file_path, self.include_patterns):
            return False

        # Check if file matches exclude patterns
        if self._matches_pattern(file_path, self.exclude_patterns):
            return False

        return True

    def _is_sqlalchemy_model(self, node: ast.ClassDef, decorator_names: Set[str]) -> bool:
        """
        Check if an AST class node represents a SQLAlchemy model.

        Detects:
        - Classes inheriting from DeclarativeBase
        - Classes inheriting from declarative_base()
        - Common SQLAlchemy base class patterns
        - Classes with @as_declarative or @declarative_base decorators
        """
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
                # Common base class names or any base if it also has a table definition
                # We are being more inclusive here; _has_table_definition will filter out non-models
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

        # If it has a __tablename__, it's likely a model even if the base name is unusual
        return False

    def _has_table_definition(self, node: ast.ClassDef) -> bool:
        """
        Check if a class has SQLAlchemy table indicators.

        Looks for:
        - __tablename__ attribute
        - __table__ attribute
        - Column definitions (Column, mapped_column)
        - Mapped[Type] annotations
        """
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
                if self._is_column_call(value):
                    return True

            if isinstance(item, ast.Assign):
                # Look for Column() or mapped_column() calls in the value
                if self._is_column_call(item.value):
                    return True

        return False

    def _is_column_call(self, node: ast.AST) -> bool:
        """Check if an AST node is a call to Column() or mapped_column()."""
        if not isinstance(node, ast.Call):
            return False
            
        func = node.func
        if isinstance(func, ast.Name):
            return func.id in ["Column", "mapped_column"]
        elif isinstance(func, ast.Attribute):
            return func.attr in ["Column", "mapped_column"]
            
        return False

    def _scan_file_for_models(self, file_path: Path) -> bool:
        """
        Scan a Python file for SQLAlchemy models using AST.

        Returns:
            True if the file contains at least one model, False otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))

            # Look for class definitions and imperative mapping calls
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's a SQLAlchemy model
                    is_model = self._is_sqlalchemy_model(node, set())
                    has_table = self._has_table_definition(node)

                    # If it has __tablename__ or __table__, it's likely a model
                    if has_table:
                        return True
                    
                    # Or if it inherits from a known model base
                    if is_model:
                        return True
                
                # Check for imperative mapping: registry.map_imperatively(Class, table)
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Attribute):
                        if func.attr == "map_imperatively":
                            return True
                    elif isinstance(func, ast.Name):
                        if func.id == "map_imperatively":
                            return True

        except (SyntaxError, UnicodeDecodeError, OSError):
            # Skip files that can't be parsed or read
            pass

        return False

    def _get_module_path(self, file_path: Path) -> Optional[str]:
        """
        Convert a file path to a Python module path.

        Example: /path/to/project/app/models/user.py -> app.models.user
        """
        try:
            # Ensure both paths are resolved to handle symlinks (like /tmp -> /private/tmp on macOS)
            abs_file_path = file_path.resolve()
            
            # Get relative path from base_path
            rel_path = abs_file_path.relative_to(self.base_path)

            # Remove .py extension
            if rel_path.suffix == ".py":
                rel_path = rel_path.with_suffix("")

            # Convert path to module notation
            parts = list(rel_path.parts)

            # Handle __init__.py files
            if parts[-1] == "__init__":
                parts = parts[:-1]

            if not parts:
                return None

            module_path = ".".join(parts)
            return module_path

        except ValueError:
            # File is not relative to base_path
            return None

    def discover(self) -> List[str]:
        """
        Discover all SQLAlchemy model modules in the codebase.

        Returns:
            List of module paths (e.g., ["app.models.user", "app.models.post"])
        """
        self._discovered_modules.clear()

        # Walk through all Python files
        for file_path in self.base_path.rglob("*.py"):
            if not self._should_scan_file(file_path):
                continue

            # Check if file contains models
            if self._scan_file_for_models(file_path):
                module_path = self._get_module_path(file_path)
                if module_path:
                    self._discovered_modules.add(module_path)

        return sorted(list(self._discovered_modules))

    def import_models(self, modules: Optional[List[str]] = None) -> int:
        """
        Import discovered model modules.

        Args:
            modules: Optional list of module paths to import. If None, imports all discovered modules.

        Returns:
            Number of successfully imported modules
        """
        if modules is None:
            modules = list(self._discovered_modules)

        imported_count = 0

        for module_path in modules:
            try:
                # Add base_path to sys.path if not already there
                base_path_str = str(self.base_path)
                if base_path_str not in sys.path:
                    sys.path.insert(0, base_path_str)

                # Import the module
                importlib.import_module(module_path)
                imported_count += 1

            except ImportError as e:
                # Log or handle import errors
                print(f"Warning: Could not import {module_path}: {e}", file=sys.stderr)
                continue

        return imported_count
