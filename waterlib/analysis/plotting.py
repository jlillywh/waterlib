"""
Plotting utilities for ResultsLogger

This module isolates matplotlib as an optional dependency. It should only be
imported when plotting functionality is actually needed.
"""

from typing import List, Optional
import pandas as pd
import matplotlib.pyplot as plt


def create_dual_axis_plot(
    df: pd.DataFrame,
    outputs: List[str],
    secondary_outputs: Optional[List[str]] = None,
    title: Optional[str] = None,
    filename: Optional[str] = None
) -> None:
    """Create dual-axis plot from DataFrame.

    This function creates publication-quality plots with optional dual Y-axes
    for comparing variables with different scales. It applies professional
    defaults including grids, legends, distinct colors, and high-resolution
    output (300 DPI).

    This function is in a separate module to isolate the matplotlib dependency.
    It should only be imported when plotting functionality is actually needed,
    keeping matplotlib as an optional dependency.

    Args:
        df: DataFrame with timesteps as index and dot-notation column names.
            The index will be used as the X-axis (typically timesteps).
        outputs: List of dot-notation identifiers for the primary Y-axis.
            These variables will be plotted with solid lines, circular markers,
            and colors from the tab10 colormap.
        secondary_outputs: Optional list of dot-notation identifiers for the
            secondary Y-axis. These variables will be plotted with dashed lines,
            square markers, and colors from the Set2 colormap. Use this to
            compare variables with different scales or units.
        title: Optional plot title. If None, a default title will be generated
            from the variable names (up to 3 variables shown explicitly).
        filename: Optional path to save the plot. If provided, the plot will be
            saved at 300 DPI with tight bounding box. If None, the plot will be
            displayed interactively using plt.show().

    Raises:
        KeyError: If any specified output identifier is not found in the DataFrame
            columns. The error message lists all available columns.
        IOError: If the plot cannot be saved to the specified filename due to
            invalid path, permission issues, or disk space problems.

    Example:
        >>> import pandas as pd
        >>> from waterlib.analysis.plotting import create_dual_axis_plot
        >>>
        >>> # Create sample data
        >>> dates = pd.date_range('2020-01-01', '2020-12-31')
        >>> df = pd.DataFrame({
        ...     'reservoir.volume': range(len(dates)),
        ...     'catchment.runoff_m3d': range(len(dates), 0, -1)
        ... }, index=dates)
        >>>
        >>> # Create dual-axis plot
        >>> create_dual_axis_plot(
        ...     df=df,
        ...     outputs=['reservoir.volume'],
        ...     secondary_outputs=['catchment.runoff_m3d'],
        ...     title='Volume vs. Runoff',
        ...     filename='plot.png'
        ... )

    Note:
        - Primary axis variables use solid lines with circular markers
        - Secondary axis variables use dashed lines with square markers
        - Colors are automatically assigned from distinct colormaps
        - Grid is enabled with 30% transparency for readability
        - Legend includes all variables from both axes
        - Tight layout prevents label clipping
        - Saved plots use 300 DPI for publication quality
    """
    # Validate that all requested outputs exist in DataFrame
    all_outputs = outputs + (secondary_outputs if secondary_outputs else [])
    missing_outputs = [out for out in all_outputs if out not in df.columns]
    if missing_outputs:
        raise KeyError(
            f"Output(s) {missing_outputs} not found in logged data.\n"
            f"Available outputs: {list(df.columns)}\n"
            f"Suggestion: Check that these outputs were logged during simulation."
        )

    # Create figure and primary axis (Requirement 4.1)
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Define distinct colors for primary vs secondary variables (Requirement 5.3)
    primary_colors = plt.cm.tab10.colors[:len(outputs)]
    secondary_colors = plt.cm.Set2.colors[:len(secondary_outputs)] if secondary_outputs else []

    # Plot primary outputs on primary Y-axis (Requirement 4.1)
    for i, output in enumerate(outputs):
        ax1.plot(df.index, df[output], label=output, marker='o', markersize=3,
                color=primary_colors[i], linewidth=2)

    ax1.set_xlabel('Timestep')
    ax1.set_ylabel('Primary Axis')

    # Add grid for readability (Requirement 5.1)
    ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)

    # Create secondary axis if secondary_outputs provided (Requirement 4.2)
    ax2 = None
    if secondary_outputs:
        ax2 = ax1.twinx()

        # Plot secondary outputs on secondary Y-axis (Requirement 4.2)
        for i, output in enumerate(secondary_outputs):
            ax2.plot(df.index, df[output], label=output, marker='s', markersize=3,
                    linestyle='--', color=secondary_colors[i], linewidth=2)

        ax2.set_ylabel('Secondary Axis')

        # Configure independent scales for both axes (Requirement 4.3)
        # This is automatic with twinx(), but we ensure proper labeling
        ax2.tick_params(axis='y')

    # Add legend with all variable labels (Requirement 5.2)
    # Combine legends from both axes if secondary axis exists
    lines1, labels1 = ax1.get_legend_handles_labels()
    if ax2:
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='best')
    else:
        ax1.legend(loc='best')

    # Use provided title or generate default from variable names (Requirement 6.1, 6.2)
    if title:
        plt.title(title)
    else:
        # Generate default title from variable names
        all_vars = outputs + (secondary_outputs if secondary_outputs else [])
        if len(all_vars) <= 3:
            default_title = ' vs '.join(all_vars)
        else:
            default_title = f"{all_vars[0]} and {len(all_vars)-1} other variables"
        plt.title(default_title)

    # Apply tight layout to prevent clipping (Requirement 5.5)
    plt.tight_layout()

    # Save to file at specified path with 300+ DPI if filename provided (Requirement 6.3, 6.4)
    if filename:
        try:
            plt.savefig(filename, dpi=300, bbox_inches='tight')
        except (IOError, OSError, PermissionError) as e:
            raise IOError(
                f"Failed to save plot to '{filename}'. "
                f"Error: {str(e)}\n"
                f"Suggestion: Check file path and write permissions."
            )
        finally:
            # Close figure to free memory
            plt.close(fig)
    else:
        # Display interactively if no filename provided (Requirement 6.5)
        plt.show()
        # Close figure after display to free memory
        plt.close(fig)
