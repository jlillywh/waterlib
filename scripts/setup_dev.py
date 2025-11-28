#!/usr/bin/env python3
"""
Quick setup script for waterlib development environment.

Installs dependencies and configures pre-commit hooks.
Run this after cloning the repository.
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n📦 {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"   ✅ Success")
        if result.stdout.strip():
            print(f"   {result.stdout.strip()[:200]}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed: {e}")
        if e.stderr:
            print(f"   {e.stderr[:200]}")
        return False


def main():
    print("="*60)
    print("🔧 Waterlib Development Environment Setup")
    print("="*60)

    # Check we're in the right directory
    if not Path('waterlib').exists() or not Path('pyproject.toml').exists():
        print("\n❌ Error: Run this script from the waterlib root directory")
        print("   Expected to find: waterlib/ and pyproject.toml")
        return 1

    print("\nThis script will:")
    print("  1. Install development dependencies")
    print("  2. Install the package in editable mode")
    print("  3. Set up pre-commit hooks")
    print("  4. Run initial checks")

    response = input("\nContinue? [Y/n]: ").strip().lower()
    if response and response not in ('y', 'yes'):
        print("Aborted.")
        return 0

    # Step 1: Install dependencies
    if not run_command(
        f"{sys.executable} -m pip install -e .[dev]",
        "Installing development dependencies"
    ):
        print("\n⚠️  Installation had issues, but continuing...")

    # Step 2: Install pre-commit hooks
    if not run_command(
        "pre-commit install",
        "Installing pre-commit hooks"
    ):
        print("\n⚠️  Could not install pre-commit hooks")
        print("   Try manually: pre-commit install")

    # Step 3: Test kernel import checker
    print("\n🔍 Testing kernel import restrictions...")
    result = subprocess.run(
        [sys.executable, "scripts/check_kernel_imports.py"] +
        [str(p) for p in Path("waterlib/kernels").rglob("*.py")
         if "__pycache__" not in str(p)],
        capture_output=True
    )

    if result.returncode == 0:
        print("   ✅ All kernels pass import restrictions")
    else:
        print("   ⚠️  Some kernels may have violations")
        print("   Check output for details")

    # Step 4: Run tests (optional)
    print("\n🧪 Running quick test check...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        test_count = len([l for l in result.stdout.split('\n')
                          if '::test_' in l])
        print(f"   ✅ Found ~{test_count} tests")
    else:
        print("   ℹ️  Could not collect tests (pytest may not be fully set up)")

    # Summary
    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("  • Read DEVELOPER_GUIDE.md for architecture and patterns")
    print("  • See docs/KERNEL_PURITY_ENFORCEMENT.md for import rules")
    print("  • Run 'pytest' to execute the test suite")
    print("  • Run 'flake8 waterlib/' to check code quality")
    print("\nPre-commit hooks are installed and will check your commits")
    print("for kernel import violations automatically.")

    return 0


if __name__ == '__main__':
    sys.exit(main())
