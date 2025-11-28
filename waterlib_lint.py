"""
Custom flake8 plugin to enforce architectural constraints.

This plugin prevents waterlib/kernels/ modules from importing from
waterlib/components/ to maintain kernel purity and enable future
performance optimizations (Rust/C++ rewrites).
"""
import ast
import os
from typing import Iterator, Tuple, Type


class KernelImportChecker:
    """
    Flake8 plugin to check that kernel modules don't import from components.

    Error Code: I900
    """
    name = "waterlib-kernel-import-checker"
    version = "1.0.0"

    I900 = (
        "I900 Kernel modules must not import from waterlib.components. "
        "Kernels must remain pure functions for scalability."
    )

    def __init__(self, tree: ast.AST, filename: str):
        self.tree = tree
        self.filename = filename

    def run(self) -> Iterator[Tuple[int, int, str, Type]]:
        """Check for forbidden imports in kernel files."""
        # Only check files in waterlib/kernels/
        normalized_path = self.filename.replace("\\", "/")
        if "waterlib/kernels/" not in normalized_path:
            return

        for node in ast.walk(self.tree):
            # Check for: from waterlib.components import ...
            if isinstance(node, ast.ImportFrom):
                if node.module and "waterlib.components" in node.module:
                    yield (
                        node.lineno,
                        node.col_offset,
                        self.I900,
                        type(self),
                    )

            # Check for: import waterlib.components...
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if "waterlib.components" in alias.name:
                        yield (
                            node.lineno,
                            node.col_offset,
                            self.I900,
                            type(self),
                        )


def check_kernel_imports(physical_line: str, filename: str) -> Iterator[Tuple[int, str]]:
    """
    Simple line-based checker for pre-commit hook compatibility.

    This is a backup/alternative approach that works without AST parsing.
    """
    normalized_path = filename.replace("\\", "/")
    if "waterlib/kernels/" not in normalized_path:
        return

    if "waterlib.components" in physical_line and ("import" in physical_line):
        yield (
            0,
            "I900 Kernel modules must not import from waterlib.components. "
            "Kernels must remain pure functions for scalability."
        )
