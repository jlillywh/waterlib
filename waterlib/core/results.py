"""
Results class for waterlib simulations.

This module provides the Results class which stores simulation outputs,
provides convenient access methods, and supports export to CSV format.
It also provides the SimulationResult dataclass for the Library-First API.
"""

from typing import Any, Dict, Optional, List
from datetime import datetime
from dataclasses import dataclass
import pandas as pd
from pathlib import Path


class Results:
    """Container for simulation results with analysis and export capabilities.

    The Results class stores all component outputs from a simulation run in a
    pandas DataFrame indexed by date. It provides methods for accessing specific
    component outputs, exporting to CSV, and calculating summary statistics.

    Attributes:
        dataframe: pandas DataFrame containing all outputs indexed by date
        metadata: Dictionary containing model info and run settings
        summary: Dictionary containing aggregate statistics
    """

    def __init__(self,
                 dataframe: pd.DataFrame,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize Results with simulation data.

        Args:
            dataframe: pandas DataFrame with dates as index and component
                      outputs as columns (format: component_name.output_name)
            metadata: Optional dictionary containing model information and
                     run settings (model name, date range, settings, etc.)

        Example:
            >>> import pandas as pd
            >>> from datetime import datetime
            >>>
            >>> # Create sample results
            >>> dates = pd.date_range('2020-01-01', '2020-01-31')
            >>> data = {
            ...     'reservoir.storage': [1000 + i*10 for i in range(31)],
            ...     'catchment.runoff': [50 + i for i in range(31)]
            ... }
            >>> df = pd.DataFrame(data, index=dates)
            >>>
            >>> results = Results(df, metadata={'model_name': 'test_model'})
        """
        self.dataframe = dataframe
        self.metadata = metadata if metadata is not None else {}
        self.summary = self._calculate_summary()

    def _calculate_summary(self) -> Dict[str, Dict[str, float]]:
        """Calculate summary statistics for all outputs.

        Computes mean, min, max, and std for each numeric column in the
        dataframe.

        Returns:
            Dictionary mapping column names to their summary statistics
        """
        summary = {}

        for col in self.dataframe.columns:
            if pd.api.types.is_numeric_dtype(self.dataframe[col]):
                summary[col] = {
                    'mean': float(self.dataframe[col].mean()),
                    'min': float(self.dataframe[col].min()),
                    'max': float(self.dataframe[col].max()),
                    'std': float(self.dataframe[col].std()),
                }

        return summary

    def get_component_output(self,
                            component_name: str,
                            output_name: str) -> pd.Series:
        """Get specific output time series for a component.

        Args:
            component_name: Name of the component
            output_name: Name of the output variable

        Returns:
            pandas Series with the output time series indexed by date

        Raises:
            KeyError: If the component.output combination doesn't exist

        Example:
            >>> results = run_simulation(model)
            >>> storage = results.get_component_output('reservoir', 'storage')
            >>> print(f"Mean storage: {storage.mean():.0f} m³")
        """
        col_name = f"{component_name}.{output_name}"

        if col_name not in self.dataframe.columns:
            available = ', '.join(self.dataframe.columns)
            raise KeyError(
                f"Output '{col_name}' not found in results. "
                f"Available outputs: {available}"
            )

        return self.dataframe[col_name]

    def to_csv(self, filepath: str) -> None:
        """Export results to CSV file.

        Saves the complete results dataframe to a CSV file with dates as the
        first column and all component outputs as subsequent columns.

        Args:
            filepath: Path to output CSV file (can be absolute or relative)

        Raises:
            IOError: If the file cannot be written

        Example:
            >>> results = run_simulation(model)
            >>> results.to_csv('simulation_results.csv')
            >>>
            >>> # Can be read back with pandas
            >>> df = pd.read_csv('simulation_results.csv', index_col=0, parse_dates=True)
        """
        try:
            # Ensure parent directory exists
            filepath_obj = Path(filepath)
            filepath_obj.parent.mkdir(parents=True, exist_ok=True)

            # Export to CSV
            self.dataframe.to_csv(filepath)

        except (IOError, OSError, PermissionError) as e:
            raise IOError(
                f"Failed to write CSV file to '{filepath}'. "
                f"Error: {str(e)}"
            )

    def plot(self, *args, **kwargs):
        """Quick plotting interface for results visualization.

        This is a convenience method that will be implemented in a future task
        to provide quick plotting capabilities.

        Args:
            *args: Positional arguments for plotting
            **kwargs: Keyword arguments for plotting

        Raises:
            NotImplementedError: This method is not yet implemented

        Note:
            For now, use waterlib.plotting functions directly with the
            results.dataframe attribute.
        """
        raise NotImplementedError(
            "Quick plotting interface not yet implemented. "
            "Use waterlib.plotting functions with results.dataframe instead."
        )

    def __repr__(self) -> str:
        """String representation of Results object."""
        n_timesteps = len(self.dataframe)
        n_outputs = len(self.dataframe.columns)

        if n_timesteps > 0:
            start_date = self.dataframe.index[0]
            end_date = self.dataframe.index[-1]
            date_info = f"from {start_date} to {end_date}"
        else:
            date_info = "empty"

        return (
            f"Results({n_timesteps} timesteps, {n_outputs} outputs, {date_info})"
        )


@dataclass
class SimulationResult:
    """Result of simulation execution for Library-First API.

    This dataclass wraps simulation results and provides paths to generated
    outputs, making it easy to access results and generated files from
    Jupyter notebooks.

    Attributes:
        csv_path: Path to exported CSV file
        dataframe: pandas DataFrame containing all outputs indexed by date
        network_diagram_path: Path to network diagram image (if generated)
        start_date: First date of simulation
        end_date: Last date of simulation
        num_timesteps: Number of timesteps executed
        components_logged: List of component names that were logged
        seeds: Dictionary mapping driver names to their seed values (for stochastic drivers)

    Example:
        >>> import waterlib
        >>> model = waterlib.load_model('model.yaml')
        >>> result = waterlib.run_simulation(model, output_dir='results/')
        >>> print(f"Results saved to: {result.csv_path}")
        >>> print(f"Simulated {result.num_timesteps} timesteps")
        >>> print(f"Seeds used: {result.seeds}")
        >>> print(result.dataframe.head())
    """
    csv_path: Path
    dataframe: pd.DataFrame
    network_diagram_path: Optional[Path]
    start_date: datetime
    end_date: datetime
    num_timesteps: int
    components_logged: List[str]
    seeds: Optional[Dict[str, Optional[int]]] = None

    def __repr__(self) -> str:
        """String representation of SimulationResult."""
        seed_info = f",\n  seeds={self.seeds}" if self.seeds else ""
        return (
            f"SimulationResult(\n"
            f"  timesteps={self.num_timesteps},\n"
            f"  components={len(self.components_logged)},\n"
            f"  date_range={self.start_date.date()} to {self.end_date.date()},\n"
            f"  csv_path={self.csv_path}{seed_info}\n"
            f")"
        )
