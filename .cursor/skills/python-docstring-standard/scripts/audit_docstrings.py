"""Dependency-free docstring coverage audit.

Walks Python files and reports every module, class, function, and method
that is missing a docstring. Mirrors the project's interrogate config:
tests are excluded and magic/dunder methods are ignored.

Usage:
    python .cursor/skills/python-docstring-standard/scripts/audit_docstrings.py [paths...]

Exits non-zero when coverage is below the threshold (default 80%).
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

DEFAULT_EXCLUDE = {"tests", ".git", ".venv", "venv", "__pycache__", "build", "dist"}


def is_magic(name: str) -> bool:
    """
    Determine whether a name is a Python double-underscore (dunder) identifier.
    
    Returns:
        `True` if `name` starts with `__` and ends with `__`, `False` otherwise.
    """
    return name.startswith("__") and name.endswith("__")


def iter_py_files(paths: list[str], exclude: set[str]) -> list[Path]:
    """
    Collect Python source files from the given file or directory paths, skipping any files whose path contains an element from `exclude`.
    
    Parameters:
        paths (list[str]): File or directory paths to scan; file paths are included directly, directory paths are searched recursively.
        exclude (set[str]): Path components to exclude (any file with a path part in this set is skipped).
    
    Returns:
        list[Path]: Sorted, deduplicated list of `Path` objects pointing to files with a `.py` suffix.
    """
    files: list[Path] = []
    for raw in paths:
        root = Path(raw)
        candidates = [root] if root.is_file() else root.rglob("*.py")
        for path in candidates:
            if path.suffix != ".py":
                continue
            if any(part in exclude for part in path.parts):
                continue
            files.append(path)
    return sorted(set(files))


def audit_file(path: Path) -> list[tuple[str, bool]]:
    """
    Collect docstring presence for the module and every class/function/async function defined in the file.
    
    For the module the entry is recorded as "<path> (module)". For classes and functions the entry is recorded as "<path>:<lineno> <qualname>", where `qualname` reflects nesting (e.g., "OuterClass.inner_func"). Dunder/magic function names are ignored; classes are recorded regardless of name. Each tuple's boolean is `True` if that node has a docstring, `False` otherwise.
    
    Returns:
        list[tuple[str, bool]]: A list of (name, has_docstring) tuples describing each audited node.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    results: list[tuple[str, bool]] = [
        (f"{path} (module)", ast.get_docstring(tree) is not None)
    ]

    def visit(node: ast.AST, prefix: str) -> None:
        """
        Traverse the AST starting at `node` and record docstring presence for nested classes and functions.
        
        Appends to the module-level `results` list one entry per encountered `ClassDef`, `FunctionDef`, or `AsyncFunctionDef` in the form (`"{path}:{lineno} {qualname}"`, `has_docstring`).
        
        Parameters:
            node (ast.AST): AST node to traverse.
            prefix (str): Qualified-name prefix to apply to discovered members (e.g., "" or "OuterClass.").
        """
        for child in ast.iter_child_nodes(node):
            if isinstance(
                child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                if isinstance(child, ast.ClassDef) or not is_magic(child.name):
                    qualname = f"{prefix}{child.name}"
                    has_doc = ast.get_docstring(child) is not None
                    results.append((f"{path}:{child.lineno} {qualname}", has_doc))
                visit(child, f"{prefix}{child.name}.")

    visit(tree, "")
    return results


def main() -> int:
    """
    Audit Python files for docstring coverage and report missing docstrings and a coverage summary.
    
    Parses command-line arguments for target paths and the `--fail-under` threshold, discovers and audits `.py` files, prints each missed docstring entry and a coverage summary line.
    
    Returns:
        int: 0 when coverage meets or exceeds the configured threshold, 1 when coverage is below the threshold.
    """
    parser = argparse.ArgumentParser(description="Audit Python docstring coverage.")
    parser.add_argument("paths", nargs="*", default=["."], help="Files or dirs.")
    parser.add_argument("--fail-under", type=float, default=80.0)
    args = parser.parse_args()

    files = iter_py_files(args.paths or ["."], DEFAULT_EXCLUDE)
    total = 0
    missed: list[str] = []
    for path in files:
        for name, has_doc in audit_file(path):
            total += 1
            if not has_doc:
                missed.append(name)

    covered = total - len(missed)
    pct = (covered / total * 100) if total else 100.0

    if missed:
        print("Missing docstrings:")
        for name in missed:
            print(f"  MISSED  {name}")
    else:
        print("No missing docstrings.")

    print(f"\nCoverage: {covered}/{total} ({pct:.1f}%) | threshold {args.fail_under}%")
    if pct < args.fail_under:
        print("RESULT: FAILED")
        return 1
    print("RESULT: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
