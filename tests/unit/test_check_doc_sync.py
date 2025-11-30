"""Tests for documentation synchronization checker."""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from check_doc_sync import determine_required_docs, check_docs_updated


def test_component_change_requires_docs():
    """Test that component changes flag required docs."""
    modified_files = ['waterlib/components/reservoir.py']
    required = determine_required_docs(modified_files)

    assert 'COMPONENTS.md' in required
    assert 'docs/API_REFERENCE.md' in required
    assert 'CHANGELOG.md' in required


def test_kernel_change_requires_docs():
    """Test that kernel changes flag required docs."""
    modified_files = ['waterlib/kernels/hydrology/awbm.py']
    required = determine_required_docs(modified_files)

    assert 'docs/API_REFERENCE.md' in required
    assert 'CHANGELOG.md' in required
    assert 'COMPONENTS.md' not in required  # Kernels don't affect components


def test_core_change_requires_docs():
    """Test that core framework changes flag required docs."""
    modified_files = ['waterlib/core/drivers.py']
    required = determine_required_docs(modified_files)

    assert 'docs/API_REFERENCE.md' in required
    assert 'DEVELOPER_GUIDE.md' in required
    assert 'CHANGELOG.md' in required


def test_climate_change_requires_docs():
    """Test that climate utility changes flag required docs."""
    modified_files = ['waterlib/climate.py']
    required = determine_required_docs(modified_files)

    assert 'README.md' in required
    assert 'docs/API_REFERENCE.md' in required
    assert 'CHANGELOG.md' in required


def test_scaffold_change_requires_docs():
    """Test that scaffold changes flag required docs."""
    modified_files = ['waterlib/core/scaffold.py']
    required = determine_required_docs(modified_files)

    assert 'GETTING_STARTED.md' in required
    assert 'CHANGELOG.md' in required


def test_all_docs_updated():
    """Test detection when all docs are updated."""
    modified_files = [
        'waterlib/components/reservoir.py',
        'COMPONENTS.md',
        'docs/API_REFERENCE.md',
        'CHANGELOG.md'
    ]
    required = determine_required_docs(modified_files)
    missing = check_docs_updated(required, modified_files)

    assert len(missing) == 0


def test_missing_docs_detected():
    """Test detection of missing documentation updates."""
    modified_files = [
        'waterlib/components/reservoir.py',
        'COMPONENTS.md'  # Missing API_REFERENCE.md and CHANGELOG.md
    ]
    required = determine_required_docs(modified_files)
    missing = check_docs_updated(required, modified_files)

    assert 'docs/API_REFERENCE.md' in missing
    assert 'CHANGELOG.md' in missing
    assert 'COMPONENTS.md' not in missing


def test_no_code_changes():
    """Test that doc-only changes don't require additional docs."""
    modified_files = ['README.md', 'CHANGELOG.md']
    required = determine_required_docs(modified_files)

    assert len(required) == 0


def test_multiple_component_changes():
    """Test that multiple component changes still flag same docs."""
    modified_files = [
        'waterlib/components/reservoir.py',
        'waterlib/components/catchment.py',
        'waterlib/components/pump.py'
    ]
    required = determine_required_docs(modified_files)

    # Should still only require these three docs (not duplicated)
    assert 'COMPONENTS.md' in required
    assert 'docs/API_REFERENCE.md' in required
    assert 'CHANGELOG.md' in required
    assert len(required) == 3
