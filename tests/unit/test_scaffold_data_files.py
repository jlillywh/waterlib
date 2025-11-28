"""
Unit tests for scaffold data file generation.

Tests the data file generation functions for WGEN params, climate timeseries, and data README.
"""

import pytest
import tempfile
from pathlib import Path

from waterlib.core.scaffold import (
    _generate_wgen_params,
    _generate_climate_timeseries,
    _generate_data_readme
)


class TestWgenParamsGeneration:
    """Tests for _generate_wgen_params function."""

    def test_creates_wgen_params_file(self):
        """Test that WGEN params file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()
            (project_root / "data").mkdir()

            _generate_wgen_params(project_root)

            wgen_path = project_root / "data" / "wgen_params.csv"
            assert wgen_path.exists()
            assert wgen_path.is_file()

    def test_wgen_params_has_12_months(self):
        """Test that WGEN params file contains 12 months of data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()
            (project_root / "data").mkdir()

            _generate_wgen_params(project_root)

            wgen_path = project_root / "data" / "wgen_params.csv"
            content = wgen_path.read_text()

            # Count data rows (excluding header and comment lines)
            # New format has header starting with 'Month,' (capital M)
            data_lines = [line for line in content.split('\n')
                         if line and not line.startswith('#') and not line.startswith('Month,')]

            assert len(data_lines) == 12

    def test_wgen_params_has_correct_columns(self):
        """Test that WGEN params file has the expected column headers for new interface."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()
            (project_root / "data").mkdir()

            _generate_wgen_params(project_root)

            wgen_path = project_root / "data" / "wgen_params.csv"
            content = wgen_path.read_text()

            # Find the header line (new format: Month,PWW,PWD,ALPHA,BETA)
            header_line = [line for line in content.split('\n')
                          if line.startswith('Month,')][0]

            # New interface has only 4 precipitation parameters per month
            expected_columns = ['Month', 'PWW', 'PWD', 'ALPHA', 'BETA']

            for col in expected_columns:
                assert col in header_line

    def test_wgen_params_has_valid_probability_values(self):
        """Test that PWW and PWD values are in valid range [0,1]."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()
            (project_root / "data").mkdir()

            _generate_wgen_params(project_root)

            wgen_path = project_root / "data" / "wgen_params.csv"
            content = wgen_path.read_text()

            # Parse data rows
            lines = content.split('\n')
            data_lines = [line for line in lines
                         if line and not line.startswith('#') and not line.startswith('Month,')]

            for line in data_lines:
                parts = line.split(',')
                if len(parts) >= 5:
                    pww = float(parts[1])
                    pwd = float(parts[2])
                    assert 0 <= pww <= 1, f"PWW {pww} out of range [0,1]"
                    assert 0 <= pwd <= 1, f"PWD {pwd} out of range [0,1]"

    def test_wgen_params_has_positive_gamma_parameters(self):
        """Test that ALPHA and BETA values are positive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()
            (project_root / "data").mkdir()

            _generate_wgen_params(project_root)

            wgen_path = project_root / "data" / "wgen_params.csv"
            content = wgen_path.read_text()

            # Parse data rows
            lines = content.split('\n')
            data_lines = [line for line in lines
                         if line and not line.startswith('#') and not line.startswith('Month,')]

            for line in data_lines:
                parts = line.split(',')
                if len(parts) >= 5:
                    alpha = float(parts[3])
                    beta = float(parts[4])
                    assert alpha > 0, f"ALPHA {alpha} must be > 0"
                    assert beta > 0, f"BETA {beta} must be > 0"


class TestClimateTimeseriesGeneration:
    """Tests for _generate_climate_timeseries function."""

    def test_creates_climate_timeseries_file(self):
        """Test that climate timeseries file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()
            (project_root / "data").mkdir()

            _generate_climate_timeseries(project_root)

            climate_path = project_root / "data" / "climate_timeseries.csv"
            assert climate_path.exists()
            assert climate_path.is_file()

    def test_climate_timeseries_has_365_days(self):
        """Test that climate timeseries file contains 365 days of data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()
            (project_root / "data").mkdir()

            _generate_climate_timeseries(project_root)

            climate_path = project_root / "data" / "climate_timeseries.csv"
            content = climate_path.read_text()

            # Count data rows (excluding header)
            lines = content.strip().split('\n')
            data_lines = lines[1:]  # Skip header

            assert len(data_lines) == 365

    def test_climate_timeseries_has_correct_columns(self):
        """Test that climate timeseries file has the expected columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()
            (project_root / "data").mkdir()

            _generate_climate_timeseries(project_root)

            climate_path = project_root / "data" / "climate_timeseries.csv"
            content = climate_path.read_text()

            # Check header
            header = content.split('\n')[0]
            expected_columns = ['date', 'precip_mm', 'tmin_c', 'tmax_c', 'et_mm']

            for col in expected_columns:
                assert col in header


class TestDataReadmeGeneration:
    """Tests for _generate_data_readme function."""

    def test_creates_data_readme_file(self):
        """Test that data README file is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()
            (project_root / "data").mkdir()

            _generate_data_readme(project_root)

            readme_path = project_root / "data" / "README.md"
            assert readme_path.exists()
            assert readme_path.is_file()

    def test_data_readme_has_content(self):
        """Test that data README file has non-empty content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_project"
            project_root.mkdir()
            (project_root / "data").mkdir()

            _generate_data_readme(project_root)

            readme_path = project_root / "data" / "README.md"
            content = readme_path.read_text()

            assert len(content) > 0
            assert "Data Directory" in content
            assert "wgen_params.csv" in content
            assert "climate_timeseries.csv" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
