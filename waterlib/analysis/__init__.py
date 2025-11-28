"""
waterlib.analysis - Analysis and visualization tools for waterlib simulations

This module provides tools for capturing, storing, and visualizing simulation results.

Classes:
    ResultsLogger: Automatically capture and store component outputs during simulation.
        Provides methods for exporting to pandas DataFrames, CSV files, and creating
        publication-quality dual-axis plots.

Example:
    >>> from waterlib import load_model, ResultsLogger
    >>> import pandas as pd
    >>>
    >>> # Load model and create logger
    >>> model = load_model('my_model.yaml')
    >>> logger = ResultsLogger(model)
    >>>
    >>> # Run simulation with logging
    >>> dates = pd.date_range('2020-01-01', '2020-12-31')
    >>> for t in dates:
    ...     model.run_step(t)
    ...     logger.log(t)
    >>>
    >>> # Export and visualize
    >>> df = logger.to_dataframe()
    >>> logger.to_csv('results.csv')
    >>> logger.plot(
    ...     outputs=['reservoir.volume'],
    ...     secondary_outputs=['catchment.runoff_m3d'],
    ...     filename='plot.png'
    ... )

Note:
    Matplotlib is an optional dependency for plotting functionality. Install it with:
    pip install matplotlib
"""

from waterlib.analysis.logger import ResultsLogger

__all__ = [
    "ResultsLogger",
]
