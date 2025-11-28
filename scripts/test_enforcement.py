"""
Test script to verify kernel import restriction enforcement.

This script creates temporary test files with violations and ensures
the enforcement mechanisms catch them correctly.
"""
import tempfile
import subprocess
import sys
from pathlib import Path


def test_flake8_detection():
    """Test that flake8 detects kernel import violations."""
    print("\n" + "="*60)
    print("TEST 1: Flake8 Detection")
    print("="*60)

    # Create temporary kernel file with violation
    test_content = """
from waterlib.components.reservoir import Reservoir

def test_function():
    pass
"""

    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        dir='waterlib/kernels',
        delete=False
    ) as f:
        f.write(test_content)
        temp_file = f.name

    try:
        # Run flake8 on the test file
        result = subprocess.run(
            ['flake8', temp_file],
            capture_output=True,
            text=True
        )

        if 'I900' in result.stdout or 'waterlib.components' in result.stdout:
            print("✅ PASS: Flake8 detected the violation")
            print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print("❌ FAIL: Flake8 did not detect the violation")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            return False
    finally:
        # Clean up
        Path(temp_file).unlink(missing_ok=True)


def test_script_detection():
    """Test that the check_kernel_imports.py script detects violations."""
    print("\n" + "="*60)
    print("TEST 2: Check Script Detection")
    print("="*60)

    # Create temporary kernel file with violation
    test_content = """import numpy as np
from waterlib.components.catchment import Catchment

def calculate_something():
    return 42
"""

    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        dir='waterlib/kernels',
        delete=False
    ) as f:
        f.write(test_content)
        temp_file = f.name

    try:
        # Run the check script
        result = subprocess.run(
            ['python', 'scripts/check_kernel_imports.py', temp_file],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print("✅ PASS: Script detected the violation and returned error code")
            print(f"   Output: {result.stderr.strip()[:200]}...")
            return True
        else:
            print("❌ FAIL: Script did not detect the violation")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            return False
    finally:
        # Clean up
        Path(temp_file).unlink(missing_ok=True)


def test_valid_imports():
    """Test that valid kernel imports pass checks."""
    print("\n" + "="*60)
    print("TEST 3: Valid Imports (Should Pass)")
    print("="*60)

    # Create temporary kernel file with VALID imports
    test_content = """import numpy as np
from dataclasses import dataclass
from typing import Tuple

from waterlib.kernels.climate.et import calculate_pet

@dataclass
class ExampleParams:
    value: float

def example_step(params: ExampleParams) -> Tuple[float, float]:
    return params.value, params.value * 2
"""

    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        dir='waterlib/kernels',
        delete=False
    ) as f:
        f.write(test_content)
        temp_file = f.name

    try:
        # Run the check script
        result = subprocess.run(
            ['python', 'scripts/check_kernel_imports.py', temp_file],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✅ PASS: Script correctly allowed valid imports")
            return True
        else:
            print("❌ FAIL: Script incorrectly flagged valid imports")
            print(f"   Output: {result.stderr}")
            return False
    finally:
        # Clean up
        Path(temp_file).unlink(missing_ok=True)


def test_existing_kernels():
    """Test that existing kernel files pass all checks."""
    print("\n" + "="*60)
    print("TEST 4: Existing Kernels (Should All Pass)")
    print("="*60)

    # Get all kernel files
    kernel_files = list(Path('waterlib/kernels').rglob('*.py'))
    kernel_files = [f for f in kernel_files if '__pycache__' not in str(f)]

    print(f"Checking {len(kernel_files)} kernel files...")

    # Run check script on all existing kernels
    result = subprocess.run(
        ['python', 'scripts/check_kernel_imports.py'] + [str(f) for f in kernel_files],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✅ PASS: All existing kernels pass import restrictions")
        return True
    else:
        print("❌ FAIL: Some existing kernels have violations")
        print(f"   Output: {result.stderr}")
        return False


def main():
    """Run all tests."""
    print("\n" + "🔬 " + "="*58)
    print("   KERNEL PURITY ENFORCEMENT TEST SUITE")
    print("="*60 + "\n")

    results = []

    # Check prerequisites
    if not Path('scripts/check_kernel_imports.py').exists():
        print("❌ ERROR: scripts/check_kernel_imports.py not found")
        print("   Run this script from the waterlib root directory")
        return 1

    if not Path('waterlib/kernels').exists():
        print("❌ ERROR: waterlib/kernels directory not found")
        return 1

    # Run tests
    try:
        results.append(("Flake8 Detection", test_flake8_detection()))
    except Exception as e:
        print(f"❌ FAIL: Flake8 test crashed: {e}")
        results.append(("Flake8 Detection", False))

    try:
        results.append(("Script Detection", test_script_detection()))
    except Exception as e:
        print(f"❌ FAIL: Script test crashed: {e}")
        results.append(("Script Detection", False))

    try:
        results.append(("Valid Imports", test_valid_imports()))
    except Exception as e:
        print(f"❌ FAIL: Valid imports test crashed: {e}")
        results.append(("Valid Imports", False))

    try:
        results.append(("Existing Kernels", test_existing_kernels()))
    except Exception as e:
        print(f"❌ FAIL: Existing kernels test crashed: {e}")
        results.append(("Existing Kernels", False))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All enforcement mechanisms are working correctly!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - check the output above")
        return 1


if __name__ == '__main__':
    sys.exit(main())
