"""
Plotting utilities for waterlib

This module provides publication-quality plotting functions for water resources
simulation results. It is designed to work directly with pandas DataFrames in
Jupyter notebooks, providing a simple API for consultants to create professional
visualizations.

The module handles matplotlib as an optional dependency with graceful error
messages, ensuring the core library remains functional even without matplotlib.
"""

from typing import Optional, List, Dict, Any, Tuple, Union
import pandas as pd


def _check_matplotlib():
    """Check if matplotlib is available and provide helpful error message.

    Returns:
        tuple: (matplotlib.pyplot, True) if available, (None, False) otherwise

    Raises:
        ImportError: With helpful message if matplotlib is not installed
    """
    try:
        import matplotlib.pyplot as plt
        return plt, True
    except ImportError:
        raise ImportError(
            "matplotlib is required for plotting functionality.\n"
            "Install it with: pip install matplotlib\n"
            "Or install waterlib with plotting support: pip install waterlib[viz]"
        )


def plot_timeseries(
    df: pd.DataFrame,
    columns: Optional[Union[str, List[str]]] = None,
    title: Optional[str] = None,
    xlabel: Optional[str] = None,
    ylabel: Optional[str] = None,
    colors: Optional[Union[str, List[str]]] = None,
    labels: Optional[Union[str, List[str]]] = None,
    linestyles: Optional[Union[str, List[str]]] = None,
    linewidths: Optional[Union[float, List[float]]] = None,
    markers: Optional[Union[str, List[str]]] = None,
    figsize: Optional[Tuple[float, float]] = None,
    grid: bool = True,
    legend: bool = True,
    filename: Optional[str] = None,
    dpi: int = 300,
    **kwargs
) -> Any:
    """Plot time series data from a pandas DataFrame.

    This function creates publication-quality time series plots with extensive
    customization options. It accepts pandas DataFrames with datetime index
    and produces professional visualizations suitable for reports and presentations.

    Args:
        df: pandas DataFrame with datetime index and numeric columns
        columns: Column name(s) to plot. If None, plots all numeric columns.
            Can be a single string or list of strings.
        title: Plot title. If None, no title is displayed.
        xlabel: X-axis label. If None, defaults to 'Date'.
        ylabel: Y-axis label. If None, no label is displayed.
        colors: Color(s) for the lines. Can be a single color or list of colors.
            Accepts matplotlib color specifications (names, hex codes, RGB tuples).
        labels: Legend label(s). Can be a single string or list of strings.
            If None, uses column names.
        linestyles: Line style(s). Can be a single style or list of styles.
            Examples: '-', '--', '-.', ':'
        linewidths: Line width(s). Can be a single float or list of floats.
        markers: Marker style(s). Can be a single marker or list of markers.
            Examples: 'o', 's', '^', 'D', None
        figsize: Figure size as (width, height) in inches. Default is (10, 6).
        grid: Whether to display grid lines. Default is True.
        legend: Whether to display legend. Default is True.
        filename: Path to save the plot. If None, displays interactively.
        dpi: Resolution for saved plots. Default is 300 (publication quality).
        **kwargs: Additional keyword arguments passed to matplotlib plot()

    Returns:
        matplotlib.figure.Figure: The created figure object

    Raises:
        ImportError: If matplotlib is not installed
        ValueError: If DataFrame is empty or columns don't exist
        TypeError: If df is not a pandas DataFrame

    Examples:
        >>> import pandas as pd
        >>> import waterlib.plotting as plotting
        >>>
        >>> # Create sample data
        >>> dates = pd.date_range('2020-01-01', periods=100)
        >>> df = pd.DataFrame({
        ...     'reservoir_storage': range(100),
        ...     'inflow': range(100, 0, -1)
        ... }, index=dates)
        >>>
        >>> # Simple plot
        >>> fig = plotting.plot_timeseries(df)
        >>>
        >>> # Customized plot
        >>> fig = plotting.plot_timeseries(
        ...     df,
        ...     columns=['reservoir_storage'],
        ...     title='Reservoir Storage Over Time',
        ...     ylabel='Storage (m³)',
        ...     colors='blue',
        ...     linestyles='--',
        ...     filename='storage.png'
        ... )
    """
    plt, _ = _check_matplotlib()

    # Validate input
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"df must be a pandas DataFrame, got {type(df)}")

    if df.empty:
        raise ValueError("DataFrame is empty, cannot create plot")

    # Handle columns parameter
    if columns is None:
        # Plot all numeric columns
        columns = df.select_dtypes(include=['number']).columns.tolist()
        if not columns:
            raise ValueError("DataFrame has no numeric columns to plot")
    elif isinstance(columns, str):
        columns = [columns]

    # Validate columns exist
    missing_cols = [col for col in columns if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Column(s) {missing_cols} not found in DataFrame.\n"
            f"Available columns: {list(df.columns)}"
        )

    # Set default figure size
    if figsize is None:
        figsize = (10, 6)

    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)

    # Normalize style parameters to lists
    n_cols = len(columns)

    if colors is not None:
        if isinstance(colors, str):
            colors = [colors] * n_cols
        elif len(colors) < n_cols:
            # Repeat colors if not enough provided
            colors = (colors * (n_cols // len(colors) + 1))[:n_cols]

    if labels is not None:
        if isinstance(labels, str):
            labels = [labels]
        elif len(labels) < n_cols:
            # Pad with column names if not enough labels
            labels = labels + columns[len(labels):]
    else:
        labels = columns

    if linestyles is not None:
        if isinstance(linestyles, str):
            linestyles = [linestyles] * n_cols
        elif len(linestyles) < n_cols:
            linestyles = (linestyles * (n_cols // len(linestyles) + 1))[:n_cols]

    if linewidths is not None:
        if isinstance(linewidths, (int, float)):
            linewidths = [linewidths] * n_cols
        elif len(linewidths) < n_cols:
            linewidths = (linewidths * (n_cols // len(linewidths) + 1))[:n_cols]

    if markers is not None:
        if isinstance(markers, str):
            markers = [markers] * n_cols
        elif len(markers) < n_cols:
            markers = (markers * (n_cols // len(markers) + 1))[:n_cols]

    # Plot each column
    for i, col in enumerate(columns):
        plot_kwargs = kwargs.copy()

        if colors is not None:
            plot_kwargs['color'] = colors[i]
        if linestyles is not None:
            plot_kwargs['linestyle'] = linestyles[i]
        if linewidths is not None:
            plot_kwargs['linewidth'] = linewidths[i]
        if markers is not None:
            plot_kwargs['marker'] = markers[i]

        ax.plot(df.index, df[col], label=labels[i], **plot_kwargs)

    # Set labels
    if title:
        ax.set_title(title)
    ax.set_xlabel(xlabel if xlabel else 'Date')
    if ylabel:
        ax.set_ylabel(ylabel)

    # Add grid
    if grid:
        ax.grid(True, alpha=0.3)

    # Add legend
    if legend and len(columns) > 0:
        ax.legend()

    # Tight layout
    plt.tight_layout()

    # Save or show
    if filename:
        plt.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close(fig)

    return fig


def plot_multiple_series(
    df: pd.DataFrame,
    series_groups: Dict[str, List[str]],
    subplot_layout: Optional[Tuple[int, int]] = None,
    titles: Optional[Dict[str, str]] = None,
    ylabels: Optional[Dict[str, str]] = None,
    figsize: Optional[Tuple[float, float]] = None,
    filename: Optional[str] = None,
    dpi: int = 300,
    **kwargs
) -> Any:
    """Create subplots for multiple series groups.

    This function creates a figure with multiple subplots, each showing a different
    group of time series. This is useful for comparing different aspects of a
    simulation (e.g., flows, storages, demands) in separate panels.

    Args:
        df: pandas DataFrame with datetime index and numeric columns
        series_groups: Dictionary mapping subplot names to lists of column names.
            Example: {'Flows': ['inflow', 'outflow'], 'Storage': ['volume']}
        subplot_layout: Tuple of (rows, cols) for subplot arrangement.
            If None, automatically determined based on number of groups.
        titles: Dictionary mapping group names to subplot titles.
            If None, uses group names as titles.
        ylabels: Dictionary mapping group names to y-axis labels.
        figsize: Figure size as (width, height) in inches.
            If None, automatically sized based on subplot layout.
        filename: Path to save the plot. If None, displays interactively.
        dpi: Resolution for saved plots. Default is 300.
        **kwargs: Additional keyword arguments passed to plot_timeseries()

    Returns:
        matplotlib.figure.Figure: The created figure object

    Raises:
        ImportError: If matplotlib is not installed
        ValueError: If series_groups is empty or columns don't exist

    Examples:
        >>> fig = plotting.plot_multiple_series(
        ...     df,
        ...     series_groups={
        ...         'Reservoir': ['reservoir.storage'],
        ...         'Flows': ['catchment.runoff', 'reservoir.outflow'],
        ...         'Demand': ['demand.supplied', 'demand.deficit']
        ...     },
        ...     titles={
        ...         'Reservoir': 'Reservoir Storage',
        ...         'Flows': 'System Flows',
        ...         'Demand': 'Water Demand'
        ...     }
        ... )
    """
    plt, _ = _check_matplotlib()

    if not series_groups:
        raise ValueError("series_groups cannot be empty")

    n_groups = len(series_groups)

    # Determine subplot layout
    if subplot_layout is None:
        # Auto-determine layout (prefer vertical stacking)
        subplot_layout = (n_groups, 1)

    rows, cols = subplot_layout

    # Determine figure size
    if figsize is None:
        figsize = (10, 4 * rows)

    # Create figure and subplots
    fig, axes = plt.subplots(rows, cols, figsize=figsize)

    # Ensure axes is always a list
    if n_groups == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    # Plot each group
    for idx, (group_name, columns) in enumerate(series_groups.items()):
        if idx >= len(axes):
            break

        ax = axes[idx]

        # Validate columns exist
        missing_cols = [col for col in columns if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"Column(s) {missing_cols} not found in DataFrame for group '{group_name}'.\n"
                f"Available columns: {list(df.columns)}"
            )

        # Plot on this subplot
        for col in columns:
            ax.plot(df.index, df[col], label=col, **kwargs)

        # Set title
        if titles and group_name in titles:
            ax.set_title(titles[group_name])
        else:
            ax.set_title(group_name)

        # Set ylabel
        if ylabels and group_name in ylabels:
            ax.set_ylabel(ylabels[group_name])

        # Add grid and legend
        ax.grid(True, alpha=0.3)
        if len(columns) > 1:
            ax.legend()

        # Only show xlabel on bottom subplot
        if idx == len(series_groups) - 1:
            ax.set_xlabel('Date')

    # Tight layout
    plt.tight_layout()

    # Save or show
    if filename:
        plt.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close(fig)

    return fig


def plot_dual_axis(
    df: pd.DataFrame,
    primary_columns: List[str],
    secondary_columns: List[str],
    title: Optional[str] = None,
    primary_ylabel: Optional[str] = None,
    secondary_ylabel: Optional[str] = None,
    primary_colors: Optional[List[str]] = None,
    secondary_colors: Optional[List[str]] = None,
    figsize: Optional[Tuple[float, float]] = None,
    filename: Optional[str] = None,
    dpi: int = 300,
    **kwargs
) -> Any:
    """Create a plot with dual y-axes for comparing variables with different scales.

    This function is useful when you want to compare variables that have very
    different magnitudes or units (e.g., flow in m³/day vs. storage in m³).

    Args:
        df: pandas DataFrame with datetime index and numeric columns
        primary_columns: List of column names for primary (left) y-axis
        secondary_columns: List of column names for secondary (right) y-axis
        title: Plot title
        primary_ylabel: Label for primary (left) y-axis
        secondary_ylabel: Label for secondary (right) y-axis
        primary_colors: Colors for primary axis lines
        secondary_colors: Colors for secondary axis lines
        figsize: Figure size as (width, height) in inches. Default is (10, 6).
        filename: Path to save the plot. If None, displays interactively.
        dpi: Resolution for saved plots. Default is 300.
        **kwargs: Additional keyword arguments passed to matplotlib plot()

    Returns:
        matplotlib.figure.Figure: The created figure object

    Raises:
        ImportError: If matplotlib is not installed
        ValueError: If columns don't exist or lists are empty

    Examples:
        >>> fig = plotting.plot_dual_axis(
        ...     df,
        ...     primary_columns=['reservoir.storage'],
        ...     secondary_columns=['catchment.runoff'],
        ...     title='Storage vs. Runoff',
        ...     primary_ylabel='Storage (m³)',
        ...     secondary_ylabel='Runoff (m³/day)'
        ... )
    """
    plt, _ = _check_matplotlib()

    if not primary_columns:
        raise ValueError("primary_columns cannot be empty")
    if not secondary_columns:
        raise ValueError("secondary_columns cannot be empty")

    # Validate columns exist
    all_columns = primary_columns + secondary_columns
    missing_cols = [col for col in all_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Column(s) {missing_cols} not found in DataFrame.\n"
            f"Available columns: {list(df.columns)}"
        )

    # Set default figure size
    if figsize is None:
        figsize = (10, 6)

    # Create figure and primary axis
    fig, ax1 = plt.subplots(figsize=figsize)

    # Plot primary columns
    for i, col in enumerate(primary_columns):
        plot_kwargs = kwargs.copy()
        if primary_colors and i < len(primary_colors):
            plot_kwargs['color'] = primary_colors[i]
        ax1.plot(df.index, df[col], label=col, **plot_kwargs)

    ax1.set_xlabel('Date')
    if primary_ylabel:
        ax1.set_ylabel(primary_ylabel)
    ax1.grid(True, alpha=0.3)

    # Create secondary axis
    ax2 = ax1.twinx()

    # Plot secondary columns
    for i, col in enumerate(secondary_columns):
        plot_kwargs = kwargs.copy()
        if secondary_colors and i < len(secondary_colors):
            plot_kwargs['color'] = secondary_colors[i]
        ax2.plot(df.index, df[col], label=col, linestyle='--', **plot_kwargs)

    if secondary_ylabel:
        ax2.set_ylabel(secondary_ylabel)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')

    if title:
        ax1.set_title(title)

    plt.tight_layout()

    # Save or show
    if filename:
        plt.savefig(filename, dpi=dpi, bbox_inches='tight')
        plt.close(fig)

    return fig


# Convenience function for quick plotting
def quick_plot(df: pd.DataFrame, *columns, **kwargs) -> Any:
    """Quick plot with minimal configuration.

    This is a convenience function for rapid visualization during interactive
    analysis. It provides sensible defaults while still accepting customization.

    Args:
        df: pandas DataFrame with datetime index
        *columns: Column names to plot (positional arguments)
        **kwargs: Keyword arguments passed to plot_timeseries()

    Returns:
        matplotlib.figure.Figure: The created figure object

    Examples:
        >>> # Plot all columns
        >>> fig = plotting.quick_plot(df)
        >>>
        >>> # Plot specific columns
        >>> fig = plotting.quick_plot(df, 'storage', 'inflow')
        >>>
        >>> # With customization
        >>> fig = plotting.quick_plot(df, 'storage', title='Storage', colors='blue')
    """
    if columns:
        kwargs['columns'] = list(columns)
    return plot_timeseries(df, **kwargs)
