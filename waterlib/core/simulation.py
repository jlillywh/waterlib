"""
Simulation engine for waterlib.

This module provides the simulation execution functionality, including the
date loop, component execution order management, and error handling.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import pandas as pd

from waterlib.core.simple_model import Model
from waterlib.core.exceptions import SimulationError
from waterlib.core.results import Results, SimulationResult


logger = logging.getLogger(__name__)


class SimulationEngine:
    """Engine for executing water model simulations.

    This class manages the simulation loop, executing components in the correct
    order for each timestep and collecting results.

    Attributes:
        model: The Model instance to simulate
        results: Dictionary storing outputs from all timesteps
    """

    def __init__(self, model: Model):
        """Initialize simulation engine with a model.

        Args:
            model: Model instance to simulate
        """
        self.model = model
        self.results: Dict[datetime, Dict[str, Dict[str, Any]]] = {}

        # Build graph and compute execution order if not already done
        if self.model.graph is None:
            self.model.build_graph()

        if not self.model.execution_order:
            self.model.compute_execution_order()

        logger.info(f"Initialized simulation engine for model '{model.name}'")

    def run(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Execute simulation from start_date to end_date.

        This method implements the main simulation loop:
        1. Iterate through each date from start_date to end_date (inclusive)
        2. For each date, execute all components in topological order
        3. Collect outputs from all components
        4. Handle any errors with clear context

        Args:
            start_date: First date of simulation (inclusive)
            end_date: Last date of simulation (inclusive)

        Returns:
            pandas DataFrame with results indexed by date, with columns for
            each component output (format: component_name.output_name)

        Raises:
            SimulationError: If an error occurs during simulation execution
        """
        logger.info(f"Starting simulation from {start_date} to {end_date}")

        # Validate date range
        if end_date < start_date:
            raise SimulationError(
                f"end_date ({end_date}) must be >= start_date ({start_date})"
            )

        # Generate date range
        current_date = start_date
        date_list = []

        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)

        logger.info(f"Simulating {len(date_list)} timesteps")

        # Execute simulation loop
        for date in date_list:
            try:
                # Execute one timestep
                timestep_results = self._execute_timestep(date)

                # Store results
                self.results[date] = timestep_results

            except Exception as e:
                # Provide clear error context
                error_msg = (
                    f"Error during simulation at date {date}: {str(e)}\n"
                    f"Component execution order: {self.model.execution_order}"
                )
                logger.error(error_msg)
                raise SimulationError(error_msg) from e

        logger.info(f"Simulation completed successfully")

        # Convert results to DataFrame
        return self._results_to_dataframe()

    def _execute_timestep(self, date: datetime) -> Dict[str, Dict[str, Any]]:
        """Execute all components for a single timestep.

        Args:
            date: Current simulation date

        Returns:
            Dictionary mapping component names to their output dictionaries

        Raises:
            SimulationError: If component execution fails
        """
        current_component = None
        component_inputs = None

        try:
            # Use the model's step method which handles climate data and execution order
            timestep_results = self.model.step(date)
            return timestep_results

        except SimulationError:
            # Already a SimulationError, just re-raise
            raise

        except Exception as e:
            # Wrap in SimulationError with context
            # Try to get more context about which component failed
            error_context = {
                'date': date.strftime('%Y-%m-%d'),
                'execution_order': self.model.execution_order,
            }

            # Try to identify the failing component
            if current_component:
                error_context['component'] = current_component

            if component_inputs:
                error_context['inputs'] = component_inputs

            raise SimulationError(
                f"Simulation failed at date {date}: {str(e)}",
                component=current_component,
                date=date.strftime('%Y-%m-%d'),
                inputs=component_inputs,
                original_error=e
            ) from e

    def _results_to_dataframe(self) -> pd.DataFrame:
        """Convert results dictionary to pandas DataFrame.

        Returns:
            DataFrame with dates as index and component outputs as columns
        """
        # Flatten results into rows
        rows = []
        dates = sorted(self.results.keys())

        for date in dates:
            row = {'date': date}

            # Add all component outputs
            for comp_name, outputs in self.results[date].items():
                if outputs is not None and isinstance(outputs, dict):
                    for output_name, value in outputs.items():
                        col_name = f"{comp_name}.{output_name}"
                        row[col_name] = value

            rows.append(row)

        # Create DataFrame
        df = pd.DataFrame(rows)

        # Set date as index
        if 'date' in df.columns:
            df = df.set_index('date')

        return df


def run_simulation(model: Model,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   output_dir: Optional[str] = None,
                   generate_plots: bool = False,
                   dry_run: bool = False) -> Optional['SimulationResult']:
    """High-level function to run a complete simulation.

    This is the main entry point for running simulations. It handles:
    - Date range extraction from model settings (if not provided)
    - Dry-run validation (if requested)
    - Simulation execution
    - Results export to CSV (if output_dir provided)
    - Optional plot generation
    - Log file creation (simulation.log in output_dir)

    Args:
        model: Model instance to simulate
        start_date: Start date (if None, uses model.settings['start_date'])
        end_date: End date (if None, uses model.settings['end_date'])
        output_dir: Optional directory to save results CSV and log file
        generate_plots: Whether to generate standard plots
        dry_run: If True, only validate model without running simulation

    Returns:
        SimulationResult object containing simulation outputs, metadata, and paths
        to generated files (None if dry_run=True)

    Raises:
        SimulationError: If simulation fails or required settings are missing

    Example:
        >>> import waterlib
        >>> model = waterlib.load_model('model.yaml')
        >>> # Validate model without running
        >>> waterlib.run_simulation(model, dry_run=True)
        >>> # Run simulation
        >>> result = waterlib.run_simulation(model, output_dir='./results')
        >>> print(f"Results saved to: {result.csv_path}")
        >>> print(result.dataframe.head())
    """
    # Set up file logging if output_dir is provided
    file_handler = None
    if output_dir is not None:
        from pathlib import Path
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        log_file = output_path / 'simulation.log'

        # Create file handler
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

        # Add handler to root logger to capture all waterlib logs
        logging.getLogger('waterlib').addHandler(file_handler)
        logger.info(f"Logging to {log_file}")

    try:
        # Extract dates from model settings if not provided
        from waterlib.core.config import ModelSettings

        if start_date is None:
            # Handle both ModelSettings and dict formats
            if isinstance(model.settings, ModelSettings):
                if model.settings.start_date is None:
                    raise SimulationError(
                        "start_date not provided and not found in model settings. "
                        "Either pass start_date parameter or include 'start_date' in YAML settings."
                    )
                start_date = model.settings.start_date
            else:
                # Legacy dict format
                if 'start_date' not in model.settings:
                    raise SimulationError(
                        "start_date not provided and not found in model settings. "
                        "Either pass start_date parameter or include 'start_date' in YAML settings."
                    )
                start_date_str = model.settings['start_date']
                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                except ValueError as e:
                    raise SimulationError(
                        f"Invalid start_date format in settings: '{start_date_str}'. "
                        f"Expected YYYY-MM-DD format."
                    ) from e

        if end_date is None:
            # Handle both ModelSettings and dict formats
            if isinstance(model.settings, ModelSettings):
                if model.settings.end_date is None:
                    raise SimulationError(
                        "end_date not provided and not found in model settings. "
                        "Either pass end_date parameter or include 'end_date' in YAML settings."
                    )
                end_date = model.settings.end_date
            else:
                # Legacy dict format
                if 'end_date' not in model.settings:
                    raise SimulationError(
                        "end_date not provided and not found in model settings. "
                        "Either pass end_date parameter or include 'end_date' in YAML settings."
                    )
                end_date_str = model.settings['end_date']
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                except ValueError as e:
                    raise SimulationError(
                        f"Invalid end_date format in settings: '{end_date_str}'. "
                        f"Expected YYYY-MM-DD format."
                    ) from e

        # Perform dry-run validation if requested
        if dry_run:
            logger.info(f"Performing dry-run validation for model '{model.name}'")
            from waterlib.core.validation import ModelValidator
            validator = ModelValidator(model)
            validator.validate(raise_on_error=True)
            logger.info("Dry-run validation passed")
            return None

        logger.info(f"Running simulation for model '{model.name}'")
        logger.info(f"Date range: {start_date} to {end_date}")

        # Create simulation engine and run
        engine = SimulationEngine(model)
        results_df = engine.run(start_date, end_date)

        # Create metadata dictionary
        metadata = {
            'model_name': model.name,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'settings': model.settings,
            'n_components': len(model.components),
            'component_names': list(model.components.keys()),
        }

        # Create Results object
        results = Results(results_df, metadata=metadata)

        # Prepare paths for SimulationResult
        csv_path = None
        network_diagram_path = None

        # Save results if output_dir provided
        if output_dir is not None:
            from pathlib import Path

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            csv_path = output_path / 'results.csv'
            results.to_csv(str(csv_path))
            logger.info(f"Results saved to {csv_path}")

            # Generate network diagram if model has visualize method
            if hasattr(model, 'visualize'):
                try:
                    network_diagram_path = output_path / 'network_diagram.png'
                    model.visualize(output_path=str(network_diagram_path), show=False)
                    logger.info(f"Network diagram saved to {network_diagram_path}")
                except Exception as e:
                    logger.warning(f"Failed to generate network diagram: {e}")
                    network_diagram_path = None

        # Generate plots if requested
        if generate_plots:
            logger.info("Plot generation requested but not yet implemented")
            # TODO: Implement standard plot generation in future task

        # Get list of components that were logged
        components_logged = list(model.components.keys())

        # Collect seed information from stochastic drivers
        seeds = {}
        if hasattr(model, 'drivers') and model.drivers:
            from waterlib.core.drivers import StochasticDriver
            for driver_name, driver in model.drivers.drivers.items():
                if isinstance(driver, StochasticDriver):
                    seeds[driver_name] = driver.seed

        # Create and return SimulationResult
        result = SimulationResult(
            csv_path=csv_path,
            dataframe=results_df,
            network_diagram_path=network_diagram_path,
            start_date=start_date,
            end_date=end_date,
            num_timesteps=len(results_df),
            components_logged=components_logged,
            seeds=seeds if seeds else None
        )

        logger.info("Simulation completed successfully")

        return result

    finally:
        # Clean up file handler
        if file_handler is not None:
            file_handler.close()
            logging.getLogger('waterlib').removeHandler(file_handler)
