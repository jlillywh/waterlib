"""
Unit tests for scaffold directory structure creation.

Tests the directory creation, cleanup, and parent directory validation functions.
"""

import pytest
import tempfile
from pathlib import Path
import shutil

from waterlib.core.scaffold import (
    _create_directory_structure,
    _cleanup_on_error,
    _validate_parent_directory
)


class TestDirectoryStructureCreation:
    """Tests for _create_directory_structure function."""

    def test_creates_all_subdirectories(self):
        """Test that all required subdirectories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()

            _create_directory_structure(project_root)

            # Check all required subdirectories exist
            assert (project_root / "models").exists()
            assert (project_root / "data").exists()
            assert (project_root / "outputs").exists()
            assert (project_root / "config").exists()

            # Check they are directories
            assert (project_root / "models").is_dir()
            assert (project_root / "data").is_dir()
            assert (project_root / "outputs").is_dir()
            assert (project_root / "config").is_dir()

    def test_idempotent_creation(self):
        """Test that calling the function twice doesn't cause errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()

            # Create once
            _create_directory_structure(project_root)

            # Create again - should not raise error
            _create_directory_structure(project_root)

            # All directories should still exist
            assert (project_root / "models").exists()
            assert (project_root / "data").exists()
            assert (project_root / "outputs").exists()
            assert (project_root / "config").exists()


class TestCleanupOnError:
    """Tests for _cleanup_on_error function."""

    def test_removes_project_directory(self):
        """Test that cleanup removes the project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()

            # Create some content
            (project_root / "test.txt").write_text("test content")
            (project_root / "subdir").mkdir()

            assert project_root.exists()

            _cleanup_on_error(project_root)

            assert not project_root.exists()

    def test_handles_nonexistent_directory(self):
        """Test that cleanup handles non-existent directories gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "nonexistent_project"

            # Should not raise error
            _cleanup_on_error(project_root)

    def test_removes_nested_structure(self):
        """Test that cleanup removes nested directory structures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()

            # Create nested structure
            _create_directory_structure(project_root)
            (project_root / "models" / "test.yaml").write_text("test: data")
            (project_root / "data" / "test.csv").write_text("a,b,c")

            assert project_root.exists()
            assert (project_root / "models" / "test.yaml").exists()

            _cleanup_on_error(project_root)

            assert not project_root.exists()


class TestValidateParentDirectory:
    """Tests for _validate_parent_directory function."""

    def test_accepts_existing_directory(self):
        """Test that validation passes for existing directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parent_dir = Path(tmpdir)

            # Should not raise error
            _validate_parent_directory(parent_dir)

    def test_rejects_nonexistent_directory(self):
        """Test that validation rejects non-existent directories."""
        nonexistent = Path("/this/path/should/not/exist/anywhere")

        with pytest.raises(FileNotFoundError) as exc_info:
            _validate_parent_directory(nonexistent)

        assert "does not exist" in str(exc_info.value)
        assert str(nonexistent) in str(exc_info.value)

    def test_rejects_file_as_parent(self):
        """Test that validation rejects files (not directories)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.txt"
            file_path.write_text("test")

            with pytest.raises(NotADirectoryError) as exc_info:
                _validate_parent_directory(file_path)

            assert "not a directory" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
