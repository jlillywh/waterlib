#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check if documentation is synchronized with code changes.

This script:
1. Gets list of modified files from git
2. Determines which documentation files need updates
3. Outputs a checklist for Kiro to verify
4. Returns exit code 1 if any docs are missing updates
"""

import subprocess
import sys
import io
from pathlib import Path
from typing import List, Set

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def get_modified_files() -> List[str]:
    """Get list of modified files from git.

    Returns:
        List of file paths that have been modified (staged and unstaged).
    """
    try:
        # Get staged files
        staged_result = subprocess.run(
            ['git', 'diff', '--name-only', '--cached'],
            capture_output=True,
            text=True,
            check=True
        )
        staged_files = [f for f in staged_result.stdout.strip().split('\n') if f]

        # Get unstaged files
        unstaged_result = subprocess.run(
            ['git', 'diff', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )
        unstaged_files = [f for f in unstaged_result.stdout.strip().split('\n') if f]

        # Combine and deduplicate
        all_files = list(set(staged_files + unstaged_files))
        return all_files
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unexpected error getting modified files: {e}", file=sys.stderr)
        return []


def determine_required_docs(modified_files: List[str]) -> Set[str]:
    """Determine which documentation files need updates based on modified code files.

    Args:
        modified_files: List of modified file paths

    Returns:
        Set of documentation file paths that should be updated
    """
    required_docs = set()

    for file in modified_files:
        # Scaffold changes (affects project templates) - check before general core
        if 'waterlib/core/scaffold.py' in file:
            required_docs.add('GETTING_STARTED.md')
            required_docs.add('CHANGELOG.md')

        # Component changes
        elif 'waterlib/components/' in file and file.endswith('.py'):
            required_docs.add('COMPONENTS.md')
            required_docs.add('docs/API_REFERENCE.md')
            required_docs.add('CHANGELOG.md')

        # Kernel changes
        elif 'waterlib/kernels/' in file and file.endswith('.py'):
            required_docs.add('docs/API_REFERENCE.md')
            required_docs.add('CHANGELOG.md')

        # Core framework changes
        elif 'waterlib/core/' in file and file.endswith('.py'):
            required_docs.add('docs/API_REFERENCE.md')
            required_docs.add('DEVELOPER_GUIDE.md')
            required_docs.add('CHANGELOG.md')

        # Climate utilities
        elif 'waterlib/climate.py' in file:
            required_docs.add('README.md')
            required_docs.add('docs/API_REFERENCE.md')
            required_docs.add('CHANGELOG.md')

    return required_docs


def check_docs_updated(required_docs: Set[str], modified_files: List[str]) -> Set[str]:
    """Check which required docs are missing from modified files.

    Args:
        required_docs: Set of documentation files that should be updated
        modified_files: List of files that have been modified

    Returns:
        Set of documentation files that are required but not yet updated
    """
    modified_set = set(modified_files)
    missing_docs = required_docs - modified_set
    return missing_docs


def main():
    """Main entry point."""
    print("🔍 Checking documentation synchronization...")

    modified_files = get_modified_files()

    if not modified_files:
        print("✅ No modified files detected")
        return 0

    print(f"\n📝 Modified files ({len(modified_files)}):")
    for file in modified_files:
        print(f"  - {file}")

    required_docs = determine_required_docs(modified_files)

    if not required_docs:
        print("\n✅ No documentation updates required")
        return 0

    missing_docs = check_docs_updated(required_docs, modified_files)

    if not missing_docs:
        print("\n✅ All required documentation is updated")
        return 0

    print("\n❌ Missing documentation updates:")
    for doc in sorted(missing_docs):
        print(f"  - {doc}")

    print("\n📋 Documentation Update Checklist:")
    print("=" * 60)

    if 'COMPONENTS.md' in missing_docs:
        print("\n[ ] COMPONENTS.md")
        print("    - Add/update parameter table for modified component")
        print("    - Update description if behavior changed")
        print("    - Add example YAML if new component")

    if 'docs/API_REFERENCE.md' in missing_docs:
        print("\n[ ] docs/API_REFERENCE.md")
        print("    - Update function signatures")
        print("    - Update parameter descriptions")
        print("    - Add new public functions/classes")

    if 'CHANGELOG.md' in missing_docs:
        print("\n[ ] CHANGELOG.md")
        print("    - Add entry under '## Unreleased'")
        print("    - Use format: '- Added/Fixed/Changed: <description>'")

    if 'DEVELOPER_GUIDE.md' in missing_docs:
        print("\n[ ] DEVELOPER_GUIDE.md")
        print("    - Update architecture diagrams if structure changed")
        print("    - Update patterns section if new pattern introduced")

    if 'README.md' in missing_docs:
        print("\n[ ] README.md")
        print("    - Update feature list if user-facing change")
        print("    - Update examples if API changed")

    if 'GETTING_STARTED.md' in missing_docs:
        print("\n[ ] GETTING_STARTED.md")
        print("    - Update project scaffolding instructions")
        print("    - Update template examples if scaffold changed")

    print("\n" + "=" * 60)
    print("\n💡 After updating docs, run this script again to verify")

    return 1


if __name__ == '__main__':
    sys.exit(main())
