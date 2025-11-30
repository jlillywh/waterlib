"""
Integration tests for project scaffolding.

Tests that generated projects work correctly end-to-end, including:
- Generated baseline.yaml can be loaded
- Generated baseline.yaml uses correct climate configuration syntax
- Generated run_model.py script is valid Python
"""

import pytest
import tempfile
from pathlib import Path
import yaml

from waterlib.core.scaffold import create_project
from waterlib.core.config import ClimateSettings


class TestScaffoldingIntegration:
    """Integration tests for create_project function."""

    def test_create_project_generates_valid_baseline_yaml(self):
        """Test that generated baseline.yaml uses correct params: syntax and can be loaded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a project
            project_path = create_project(
                "test_project",
                parent_dir=tmpdir,
                include_examples=True
            )

            # Check that baseline.yaml exists
            baseline_path = project_path / "models" / "baseline.yaml"
            assert baseline_path.exists(), "baseline.yaml should be generated"

            # Load the YAML file
            with open(baseline_path, 'r') as f:
                yaml_content = yaml.safe_load(f)

            # Verify climate configuration structure
            assert 'settings' in yaml_content
            assert 'climate' in yaml_content['settings']
            climate = yaml_content['settings']['climate']

            # Check precipitation configuration uses WGEN
            assert 'precipitation' in climate
            precip = climate['precipitation']
            assert precip['mode'] == 'wgen'

            # Check for WGEN configuration
            assert 'wgen_config' in climate
            wgen = climate['wgen_config']
            assert 'param_file' in wgen

            # Check site configuration (latitude/elevation are now in site: block)
            assert 'site' in yaml_content
            site = yaml_content['site']
            assert 'latitude' in site
            assert 'elevation_m' in site

    def test_generated_baseline_yaml_loads_successfully(self):
        """Test that generated baseline.yaml can be loaded by ClimateSettings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a project
            project_path = create_project(
                "test_project",
                parent_dir=tmpdir,
                include_examples=True
            )

            # Load the baseline.yaml
            baseline_path = project_path / "models" / "baseline.yaml"

            with open(baseline_path, 'r') as f:
                yaml_content = yaml.safe_load(f)

            # Extract climate configuration
            climate_dict = yaml_content['settings']['climate']

            # This should not raise any errors
            climate = ClimateSettings.from_dict(climate_dict)

            # Verify precipitation driver was parsed correctly
            precip = climate.precipitation
            assert precip is not None
            assert precip.mode == 'wgen'

            # Verify temperature driver uses WGEN
            temp = climate.temperature
            assert temp is not None
            assert temp.mode == 'wgen'

            # Verify WGEN configuration exists and has required parameters
            assert climate.wgen_config is not None
            assert hasattr(climate.wgen_config, 'latitude')
            assert hasattr(climate.wgen_config, 'param_file')
            assert hasattr(climate.wgen_config, 'elevation_m')

    def test_generated_run_model_script_is_valid_python(self):
        """Test that generated run_model.py is valid Python syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a project
            project_path = create_project(
                "test_project",
                parent_dir=tmpdir,
                include_examples=True
            )

            # Check that run_model.py exists
            script_path = project_path / "run_model.py"
            assert script_path.exists(), "run_model.py should be generated"

            # Try to compile the script (checks for syntax errors)
            script_content = script_path.read_text()
            compile(script_content, str(script_path), 'exec')

    def test_create_project_without_examples(self):
        """Test that create_project works with include_examples=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a project without examples
            project_path = create_project(
                "minimal_project",
                parent_dir=tmpdir,
                include_examples=False
            )

            # Check that directory structure exists
            assert (project_path / "models").exists()
            assert (project_path / "data").exists()
            assert (project_path / "outputs").exists()
            assert (project_path / "config").exists()

            # Check that example files were NOT created
            assert not (project_path / "README.md").exists()
            assert not (project_path / "models" / "baseline.yaml").exists()
            assert not (project_path / "run_model.py").exists()
            assert not (project_path / "data" / "wgen_params.csv").exists()

    def test_create_project_with_overwrite(self):
        """Test that create_project can overwrite existing projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a project
            project_path = create_project(
                "test_project",
                parent_dir=tmpdir,
                include_examples=True
            )

            # Create a marker file
            marker_file = project_path / "marker.txt"
            marker_file.write_text("original")

            # Recreate with overwrite=True
            project_path2 = create_project(
                "test_project",
                parent_dir=tmpdir,
                include_examples=True,
                overwrite=True
            )

            # Check that it's the same path
            assert project_path == project_path2

            # Check that marker file is gone (project was recreated)
            assert not marker_file.exists()

            # Check that new files exist
            assert (project_path / "models" / "baseline.yaml").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
