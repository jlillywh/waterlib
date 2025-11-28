#!/usr/bin/env python3
"""
Architecture enforcement script for waterlib v1.2.

Ensures the "Kernel Purity" rule: kernel files must not import from components.
This maintains the one-way dependency flow and enables future Rust/C++ migration.
"""
import ast
import sys
import glob


def check_imports(file_path):
    """Check a single file for forbidden imports.

    Args:
        file_path: Path to Python file to check

    Returns:
        Error message if violation found, None otherwise
    """
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)

    for node in ast.walk(tree):
        # Check 'import waterlib.components...'
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("waterlib.components"):
                    return f"Line {node.lineno}: import {alias.name}"

        # Check 'from waterlib.components import ...'
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("waterlib.components"):
                return f"Line {node.lineno}: from {node.module} import ..."
    return None


def main():
    """Main entry point for kernel purity check."""
    kernel_files = glob.glob("waterlib/kernels/**/*.py", recursive=True)
    violations = []

    for file_path in kernel_files:
        error = check_imports(file_path)
        if error:
            violations.append(f"{file_path}: {error}")

    if violations:
        print("[FAIL] ARCHITECTURE VIOLATION: Kernels must not import Components.")
        for v in violations:
            print(f"  - {v}")
        sys.exit(1)

    print("[PASS] Kernel purity check passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
