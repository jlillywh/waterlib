"""
End-to-end workflow test for waterlib project scaffolding.

Tests the complete user workflow:
1. Create a new project with create_project()
2. Load the generated model with load_model()
3. Run the simulation with run_simulation()
4. Verify outputs are generated correctly
5. Verify network diagram shows connections

This test ensures the entire user experience works correctly from
project creation through model execution.
"""

import pytest
import tempfile
from pathlib import Path
import shutil

import waterlib


class TestEndToEndWorkflow:
    """End-to-end tests for complete user workflow."""

    def test_complete_workflow_creates_and_runs_model(self):
        """Test complete workflow: create project -> load model -> run simulation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Create a new project
            project_path = waterlib.create_project(
                "test_model",
                parent_dir=tmpdir,
                include_examples=True
            )

            assert project_path.exists()
            assert (project_path / "models" / "baseline.yaml").exists()
            assert (project_path / "run_model.py").exists()

            # Step 2: Load the generated model
            model_file = project_path / "models" / "baseline.yaml"
            model = waterlib.load_model(str(model_file))

            assert model is not None
            assert isinstance(model, waterlib.Model)
            assert len(model.components) > 0

            # Verify expected components exist
            assert "catchment" in model.components
            assert "reservoir" in model.components
            assert "demand" in model.components

            # Step 3: Run the simulation
            output_dir = project_path / "outputs"
            output_dir.mkdir(exist_ok=True)

            results = waterlib.run_simulation(model, output_dir=str(output_dir))

            # Step 4: Verify results
            assert results is not None
            assert results.num_timesteps > 0
            assert results.dataframe is not None
            assert len(results.dataframe) > 0

            # Verify CSV output was created
            assert results.csv_path is not None
            assert Path(results.csv_path).exists()

            # Verify network diagram was created
            assert results.network_diagram_path is not None
            network_diagram = Path(results.network_diagram_path)
            assert network_diagram.exists()
            assert network_diagram.name == "network_diagram.png"

            # Step 5: Verify component outputs exist in dataframe
            df = results.dataframe
            assert "catchment.runoff" in df.columns
            assert "reservoir.storage" in df.columns
            assert "demand.demand" in df.columns
            assert "demand.supplied" in df.columns

    def test_model_graph_has_connections(self):
        """Test that the generated model's graph contains the expected edges."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create project
            project_path = waterlib.create_project(
                "test_model",
                parent_dir=tmpdir,
                include_examples=True
            )

            # Load model
            model_file = project_path / "models" / "baseline.yaml"
            model = waterlib.load_model(str(model_file))

            # Build graph
            graph = model.build_graph()

            # Verify graph has nodes
            assert len(graph.nodes()) >= 3
            assert "catchment" in graph.nodes()
            assert "reservoir" in graph.nodes()
            assert "demand" in graph.nodes()

            # Verify graph has edges (connections)
            assert len(graph.edges()) >= 2, "Graph should have at least 2 edges"

            # Verify specific connections exist
            # catchment -> reservoir (via inflows)
            assert graph.has_edge("catchment", "reservoir"), \
                "Should have edge from catchment to reservoir"

            # reservoir -> demand (via source)
            assert graph.has_edge("reservoir", "demand"), \
                "Should have edge from reservoir to demand"

    def test_network_visualization_generates_without_error(self):
        """Test that network visualization can be generated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create project
            project_path = waterlib.create_project(
                "test_model",
                parent_dir=tmpdir,
                include_examples=True
            )

            # Load model
            model_file = project_path / "models" / "baseline.yaml"
            model = waterlib.load_model(str(model_file))

            # Generate visualization
            output_path = project_path / "test_diagram.png"

            # This should not raise an error
            try:
                model.visualize(
                    output_path=str(output_path),
                    show=False
                )

                # Verify file was created
                assert output_path.exists()
                assert output_path.stat().st_size > 0
            except ImportError as e:
                # matplotlib might not be installed in test environment
                if "matplotlib" not in str(e):
                    raise
                pytest.skip("matplotlib not available for visualization test")

    def test_execution_order_is_computed(self):
        """Test that execution order is computed correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create project
            project_path = waterlib.create_project(
                "test_model",
                parent_dir=tmpdir,
                include_examples=True
            )

            # Load model
            model_file = project_path / "models" / "baseline.yaml"
            model = waterlib.load_model(str(model_file))

            # Build graph and compute execution order
            model.build_graph()
            execution_order = model.compute_execution_order()

            # Verify execution order is sensible
            assert len(execution_order) == len(model.components)

            # catchment should come before reservoir (topological order)
            catchment_idx = execution_order.index("catchment")
            reservoir_idx = execution_order.index("reservoir")
            assert catchment_idx < reservoir_idx, \
                "Catchment should execute before reservoir"

            # reservoir should come before demand
            demand_idx = execution_order.index("demand")
            assert reservoir_idx < demand_idx, \
                "Reservoir should execute before demand"

    def test_cleanup_removes_test_project(self):
        """Test that temporary test projects can be cleaned up."""
        # This test demonstrates cleanup pattern
        tmpdir = Path(tempfile.mkdtemp())

        try:
            # Create project
            project_path = waterlib.create_project(
                "test_model",
                parent_dir=str(tmpdir),
                include_examples=True
            )

            assert project_path.exists()

            # Cleanup
            shutil.rmtree(tmpdir)

            # Verify cleanup
            assert not tmpdir.exists()
            assert not project_path.exists()

        except Exception as e:
            # Ensure cleanup even if test fails
            if tmpdir.exists():
                shutil.rmtree(tmpdir)
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
