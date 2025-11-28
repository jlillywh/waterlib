"""
ResultsLogger - Automatic capture and visualization of simulation results

The ResultsLogger class provides a streamlined interface for capturing component
outputs during simulation, exporting data to pandas DataFrames, and creating
publication-quality visualizations.
"""

from typing import Any, Dict, List, Optional
import pandas as pd


class ResultsLogger:
    """Captures and stores simulation results from waterlib models.

    The logger automatically discovers component outputs on first use and
    efficiently captures their values at each timestep. It provides methods
    for exporting data to pandas DataFrames and creating dual-axis plots.

    Attributes:
        _model: Reference to the WaterModel being tracked
        _components_to_track: List of component names to log
        _schema: Mapping of component names to their output names
        _schema_discovered: Flag indicating if schema discovery has occurred
        _timesteps: Ordered list of logged timesteps
        _data: Dictionary mapping dot-notation IDs to value lists
    """

    def __init__(self, model: Any, components: Optional[List[str]] = None):
        """Initialize logger with model reference.

        The logger stores a reference to the model and identifies which components
        to track. Schema discovery (identifying available outputs) is deferred until
        the first call to log() to avoid the "empty output trap" where components'
        _outputs dictionaries are empty at initialization.

        Args:
            model: WaterModel instance to track. The model should contain at least
                one component with outputs.
            components: Optional list of component names to track. If None, all
                components in the model will be tracked. Use this parameter to
                reduce memory usage in large models or long simulations.

        Raises:
            ValueError: If any specified component name doesn't exist in the model.
                The error message will list all available component names.

        Example:
            >>> from waterlib import load_model, ResultsLogger
            >>> model = load_model('my_model.yaml')
            >>>
            >>> # Track all components
            >>> logger = ResultsLogger(model)
            >>>
            >>> # Track only specific components
            >>> logger = ResultsLogger(model, components=['reservoir', 'demand'])

        Note:
            The logger does not validate that components have outputs at initialization.
            If no outputs are found during the first log() call, a RuntimeWarning
            will be raised.
        """
        # Store model reference (Requirement 1.1)
        self._model = model

        # Identify all components in model (Requirement 1.2)
        available_components = list(model.components.keys())

        # Handle optional components parameter for selective logging (Requirement 1.4)
        if components is None:
            # Track all components if none specified
            self._components_to_track = available_components
        else:
            # Validate all specified components exist in model (Requirement 1.5)
            invalid_components = [c for c in components if c not in available_components]
            if invalid_components:
                raise ValueError(
                    f"Component(s) {invalid_components} not found in model.\n"
                    f"Available components: {available_components}\n"
                    f"Suggestion: Check component names in your YAML configuration."
                )
            self._components_to_track = components

        # Initialize empty data structures (Requirement 1.3)
        self._schema: Dict[str, List[str]] = {}
        self._schema_discovered: bool = False
        self._timesteps: List[Any] = []
        self._data: Dict[str, List[Any]] = {}

    def log(self, timestep: Any) -> None:
        """Capture current state of all tracked components.

        This method should be called after each model.run_step(t) to record the
        current state of all tracked components. On the first call, it performs
        schema discovery by inspecting each component's _outputs dictionary to
        identify available outputs. On subsequent calls, it uses the cached schema
        for efficient value retrieval.

        The method executes with constant time complexity relative to simulation
        duration (O(1) with respect to number of timesteps), making it suitable
        for long simulations (20,000-40,000 timesteps).

        Args:
            timestep: Current simulation time. Can be any type (datetime, int, str).
                This value will be used as the DataFrame index when exporting data.

        Raises:
            RuntimeWarning: If schema discovery finds no outputs. This typically
                occurs when log() is called before run_step(), meaning components
                haven't populated their _outputs dictionaries yet.
            KeyError: If a previously discovered output is no longer available on
                a component. This can happen if component outputs change after
                schema discovery.

        Example:
            >>> import pandas as pd
            >>> from waterlib import load_model, ResultsLogger
            >>>
            >>> model = load_model('my_model.yaml')
            >>> logger = ResultsLogger(model)
            >>>
            >>> # Run simulation with logging
            >>> dates = pd.date_range('2020-01-01', '2020-12-31')
            >>> for t in dates:
            ...     model.run_step(t)
            ...     logger.log(t)  # Capture state after each step

        Note:
            - Always call run_step() before log() to ensure outputs are populated
            - The first call to log() may be slightly slower due to schema discovery
            - Subsequent calls use cached schema for optimal performance
        """
        # Perform schema discovery on first call (Requirement 2.1)
        if not self._schema_discovered:
            # Inspect _outputs dictionaries of all tracked components
            for component_name in self._components_to_track:
                component = self._model.components[component_name]

                # Get output names from component's _outputs dictionary
                output_names = list(component._outputs.keys())

                # Store in schema mapping
                if output_names:
                    self._schema[component_name] = output_names

            # Raise RuntimeWarning if schema is empty (Requirement 2.1)
            if not self._schema:
                import warnings
                warnings.warn(
                    "Schema discovery found no outputs. "
                    "Ensure run_step() has been called before log().",
                    RuntimeWarning
                )

            # Mark schema as discovered (Requirement 2.2)
            self._schema_discovered = True

            # Initialize data storage for each output using dot-notation (Requirement 2.5)
            for component_name, output_names in self._schema.items():
                for output_name in output_names:
                    dot_notation_key = f"{component_name}.{output_name}"
                    self._data[dot_notation_key] = []

        # Capture values for all tracked outputs (Requirement 2.3)
        for component_name, output_names in self._schema.items():
            component = self._model.components[component_name]

            for output_name in output_names:
                # Retrieve current value using get_value()
                try:
                    value = component.get_value(output_name)
                except KeyError:
                    raise KeyError(
                        f"Output '{output_name}' no longer available on component '{component_name}'. "
                        f"Component outputs may have changed after schema discovery."
                    )

                # Store value using dot-notation key (Requirement 2.5)
                dot_notation_key = f"{component_name}.{output_name}"
                self._data[dot_notation_key].append(value)

        # Associate values with provided timestep (Requirement 2.4)
        self._timesteps.append(timestep)

    def to_dataframe(self) -> pd.DataFrame:
        """Export logged data as pandas DataFrame.

        Converts the internal columnar storage format to a pandas DataFrame with
        timesteps as the index and dot-notation identifiers as column names. The
        chronological order of timesteps is preserved.

        Returns:
            pd.DataFrame: DataFrame containing all logged data. The index contains
                the timesteps in the order they were logged. Column names use
                dot-notation format (e.g., 'reservoir.volume', 'catchment.runoff_m3d').
                If no data has been logged, returns an empty DataFrame.

        Example:
            >>> from waterlib import load_model, ResultsLogger
            >>> import pandas as pd
            >>>
            >>> model = load_model('my_model.yaml')
            >>> logger = ResultsLogger(model)
            >>>
            >>> # Run simulation
            >>> dates = pd.date_range('2020-01-01', '2020-01-31')
            >>> for t in dates:
            ...     model.run_step(t)
            ...     logger.log(t)
            >>>
            >>> # Export to DataFrame
            >>> df = logger.to_dataframe()
            >>> print(df.shape)  # (31, N) where N is number of outputs
            >>> print(df.columns)  # ['reservoir.volume', 'reservoir.elevation', ...]
            >>>
            >>> # Perform custom analysis
            >>> mean_volume = df['reservoir.volume'].mean()
            >>> max_runoff = df['catchment.runoff_m3d'].max()

        Note:
            The DataFrame is created from the internal storage on each call, so
            repeated calls will create new DataFrame objects. For large datasets,
            consider storing the result if you need to access it multiple times.
        """
        # Handle empty data case (Requirement 3.5)
        if not self._timesteps:
            return pd.DataFrame()

        # Convert internal _data dictionary to pandas DataFrame (Requirement 3.1)
        # Use dot-notation identifiers as column names (Requirement 3.3)
        df = pd.DataFrame(self._data)

        # Use _timesteps as DataFrame index (Requirement 3.2)
        # Preserve timestep order (Requirement 3.4)
        df.index = self._timesteps

        return df

    def to_csv(self, filename: str) -> None:
        """Export logged data to CSV file.

        Converts the logged data to a pandas DataFrame and exports it to a CSV file.
        The CSV will have timesteps in the first column and dot-notation identifiers
        as column headers.

        Args:
            filename: Path to output CSV file. Can be absolute or relative. Parent
                directories must exist.

        Raises:
            IOError: If the file cannot be written due to invalid path, permission
                issues, or disk space problems. The error message will include the
                problematic path and suggestions for resolution.

        Example:
            >>> from waterlib import load_model, ResultsLogger
            >>> import pandas as pd
            >>>
            >>> model = load_model('my_model.yaml')
            >>> logger = ResultsLogger(model)
            >>>
            >>> # Run simulation
            >>> dates = pd.date_range('2020-01-01', '2020-12-31')
            >>> for t in dates:
            ...     model.run_step(t)
            ...     logger.log(t)
            >>>
            >>> # Export to CSV
            >>> logger.to_csv('results.csv')
            >>>
            >>> # The CSV can be read back with pandas
            >>> df = pd.read_csv('results.csv', index_col=0)

        Note:
            The CSV format is suitable for sharing with external tools, importing
            into spreadsheet applications, or archiving results. For programmatic
            analysis within Python, consider using to_dataframe() instead.
        """
        # Call to_dataframe() to get DataFrame
        df = self.to_dataframe()

        # Export DataFrame to CSV using pandas
        try:
            df.to_csv(filename)
        except (IOError, OSError, PermissionError) as e:
            raise IOError(
                f"Failed to write CSV file to '{filename}'. "
                f"Error: {str(e)}\n"
                f"Suggestion: Check file path and write permissions."
            )

    def plot(self,
             outputs: List[str],
             secondary_outputs: Optional[List[str]] = None,
             title: Optional[str] = None,
             filename: Optional[str] = None) -> None:
        """Create dual-axis plot of logged data.

        Creates publication-quality plots with optional dual Y-axes for comparing
        variables with different scales. The plot includes grids, legends, and uses
        distinct colors for primary vs. secondary variables. Plots are saved at
        300 DPI for publication quality.

        This method requires matplotlib to be installed. Matplotlib is imported
        lazily (only when plot() is called) to keep it as an optional dependency.

        Args:
            outputs: List of dot-notation identifiers for the primary Y-axis.
                These variables will be plotted with solid lines and circular markers.
                Example: ['reservoir.volume', 'reservoir.elevation']
            secondary_outputs: Optional list of dot-notation identifiers for the
                secondary Y-axis. These variables will be plotted with dashed lines
                and square markers. Use this to compare variables with different
                scales (e.g., volume in m³ vs. flow in m³/day).
                Example: ['catchment.runoff_m3d', 'demand.delivered_m3d']
            title: Optional plot title. If None, a default title will be generated
                from the variable names.
            filename: Optional path to save the plot. If provided, the plot will be
                saved to this file at 300 DPI. If None, the plot will be displayed
                interactively. Supported formats: PNG, PDF, SVG, etc.

        Raises:
            ImportError: If matplotlib is not installed. The error message includes
                installation instructions.
            KeyError: If any specified output identifier was not logged. The error
                message lists all available output identifiers.
            IOError: If the plot cannot be saved to the specified filename due to
                invalid path or permission issues.

        Example:
            >>> from waterlib import load_model, ResultsLogger
            >>> import pandas as pd
            >>>
            >>> model = load_model('my_model.yaml')
            >>> logger = ResultsLogger(model)
            >>>
            >>> # Run simulation
            >>> dates = pd.date_range('2020-01-01', '2020-12-31')
            >>> for t in dates:
            ...     model.run_step(t)
            ...     logger.log(t)
            >>>
            >>> # Single-axis plot
            >>> logger.plot(
            ...     outputs=['reservoir.volume'],
            ...     title='Reservoir Volume Over Time',
            ...     filename='volume.png'
            ... )
            >>>
            >>> # Dual-axis plot (comparing different scales)
            >>> logger.plot(
            ...     outputs=['reservoir.volume'],
            ...     secondary_outputs=['catchment.runoff_m3d'],
            ...     title='Reservoir Volume vs. Catchment Runoff',
            ...     filename='volume_vs_runoff.png'
            ... )
            >>>
            >>> # Multiple variables on each axis
            >>> logger.plot(
            ...     outputs=['reservoir.volume', 'reservoir.elevation'],
            ...     secondary_outputs=['catchment.runoff_m3d', 'demand.delivered_m3d'],
            ...     title='Reservoir State and Flow Metrics'
            ... )

        Note:
            - Install matplotlib with: pip install matplotlib
            - Or install waterlib with visualization support: pip install waterlib[viz]
            - Dual-axis plots are ideal for comparing variables with different units
            - All plots include grids, legends, and use publication-quality defaults
            - Saved plots use 300 DPI for high-resolution output
        """
        # Lazy import of plotting module (Requirement 7.5)
        # Import only when plot() is called to minimize overhead
        try:
            from waterlib.analysis.plotting import create_dual_axis_plot
        except ImportError:
            raise ImportError(
                "matplotlib is required for plotting. "
                "Install it with: pip install matplotlib\n"
                "Or install waterlib with visualization support: pip install waterlib[viz]"
            )

        # Validate all requested outputs were logged (Requirement 4.5)
        all_requested = outputs + (secondary_outputs if secondary_outputs else [])
        available_outputs = list(self._data.keys())
        invalid_outputs = [out for out in all_requested if out not in available_outputs]

        if invalid_outputs:
            raise KeyError(
                f"Output(s) {invalid_outputs} not found in logged data.\n"
                f"Available outputs: {available_outputs}\n"
                f"Suggestion: Check that these outputs were logged during simulation."
            )

        # Convert logged data to DataFrame (Requirement 4.1, 4.4)
        df = self.to_dataframe()

        # Call create_dual_axis_plot() with data and parameters (Requirement 4.1, 4.4)
        create_dual_axis_plot(
            df=df,
            outputs=outputs,
            secondary_outputs=secondary_outputs,
            title=title,
            filename=filename
        )
