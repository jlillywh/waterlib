"""
Simplified Model class for waterlib following the new design.

This module provides a clean, simplified Model class that holds components
and connections, with a focus on the library-first approach.
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import logging
import networkx as nx

from waterlib.core.base import Component
from waterlib.climate import ClimateManager
from waterlib.core.config import ModelSettings


logger = logging.getLogger(__name__)


class Model:
    """Container for a complete water simulation model.

    This class represents a fully-loaded water model with all components
    instantiated and connected according to the YAML configuration.

    Attributes:
        name: Model name from YAML
        description: Model description from YAML
        components: Dictionary mapping component names to component instances
        connections: List of connection specifications
        settings: Dictionary of simulation settings (dates, climate, etc.)
        graph: networkx.DiGraph representing component connections
        execution_order: List of component names in topological execution order
    """

    def __init__(self,
                 name: str = "Unnamed Model",
                 description: str = "",
                 components: Optional[Dict[str, Component]] = None,
                 connections: Optional[List[Dict[str, str]]] = None,
                 settings: Optional[ModelSettings] = None,
                 yaml_dir: Optional[Path] = None):
        """Initialize Model with components and connections.

        Args:
            name: Model name
            description: Model description
            components: Dictionary of component instances
            connections: List of connection specifications (optional)
            settings: ModelSettings instance with simulation settings
            yaml_dir: Directory containing YAML file (for resolving relative paths)
        """
        self.name = name
        self.description = description
        self.components = components or {}
        self.connections = connections or []
        self.settings = settings or ModelSettings.from_dict({})

        self.yaml_dir = yaml_dir or Path.cwd()
        self.graph: Optional[nx.DiGraph] = None
        self.execution_order: List[str] = []

        # Initialize climate manager if climate settings are present
        self.climate_manager: Optional[ClimateManager] = None

        climate_config = None
        if self.settings.climate is not None:
            # Convert ClimateSettings to dict for ClimateManager
            climate_dict = {}
            if self.settings.climate.precipitation:
                climate_dict['precipitation'] = {
                    'mode': self.settings.climate.precipitation.mode,
                    'seed': self.settings.climate.precipitation.seed,
                    'file': self.settings.climate.precipitation.file,
                    'column': self.settings.climate.precipitation.column
                }
            if self.settings.climate.temperature:
                climate_dict['temperature'] = {
                    'mode': self.settings.climate.temperature.mode,
                    'seed': self.settings.climate.temperature.seed,
                    'file': self.settings.climate.temperature.file,
                    'column': self.settings.climate.temperature.column
                }
            if self.settings.climate.et:
                climate_dict['et'] = {
                    'mode': self.settings.climate.et.mode,
                    'seed': self.settings.climate.et.seed,
                    'file': self.settings.climate.et.file,
                    'column': self.settings.climate.et.column
                }
            if self.settings.climate.wgen_config:
                # Convert WgenConfig to dict for ClimateManager
                wgen_dict = {
                    'param_file': self.settings.climate.wgen_config.param_file,
                    'latitude': self.settings.climate.wgen_config.latitude,
                    'elevation_m': self.settings.climate.wgen_config.elevation_m,
                    'txmd': self.settings.climate.wgen_config.txmd,
                    'txmw': self.settings.climate.wgen_config.txmw,
                    'tn': self.settings.climate.wgen_config.tn,
                    'atx': self.settings.climate.wgen_config.atx,
                    'atn': self.settings.climate.wgen_config.atn,
                    'cvtx': self.settings.climate.wgen_config.cvtx,
                    'acvtx': self.settings.climate.wgen_config.acvtx,
                    'cvtn': self.settings.climate.wgen_config.cvtn,
                    'acvtn': self.settings.climate.wgen_config.acvtn,
                    'dt_day': self.settings.climate.wgen_config.dt_day,
                    'seed': self.settings.climate.wgen_config.seed
                }
                # Add optional parameters if present
                if self.settings.climate.wgen_config.rs_mean is not None:
                    wgen_dict['rs_mean'] = self.settings.climate.wgen_config.rs_mean
                if self.settings.climate.wgen_config.rs_amplitude is not None:
                    wgen_dict['rs_amplitude'] = self.settings.climate.wgen_config.rs_amplitude
                if self.settings.climate.wgen_config.rs_cv is not None:
                    wgen_dict['rs_cv'] = self.settings.climate.wgen_config.rs_cv
                if self.settings.climate.wgen_config.rs_wet_factor is not None:
                    wgen_dict['rs_wet_factor'] = self.settings.climate.wgen_config.rs_wet_factor
                if self.settings.climate.wgen_config.min_rain_mm is not None:
                    wgen_dict['min_rain_mm'] = self.settings.climate.wgen_config.min_rain_mm
                climate_dict['wgen_config'] = wgen_dict
            climate_config = climate_dict

        if climate_config:
            self.climate_manager = ClimateManager(
                climate_config,
                yaml_dir=self.yaml_dir
            )
            logger.info("Initialized ClimateManager for global climate utilities")

        logger.info(f"Initialized model '{name}' with {len(self.components)} components")

    def build_graph(self) -> nx.DiGraph:
        """Build networkx directed graph from component connections.

        Creates a directed graph where nodes represent components and edges
        represent dependencies from inline connection specifications (inflows,
        source, etc.) that are set on components during YAML loading.

        Returns:
            networkx.DiGraph with components as nodes and connections as edges
        """
        graph = nx.DiGraph()

        # Add all components as nodes
        for name, component in self.components.items():
            graph.add_node(
                name,
                component=component,
                type=component.__class__.__name__
            )

        # Add edges from inline connection specifications on components
        for name, component in self.components.items():
            # Check for inflows attribute (list of source components)
            if hasattr(component, 'inflow_getters') and component.inflow_getters:
                for source_comp, _ in component.inflow_getters:
                    if source_comp.name in self.components:
                        graph.add_edge(source_comp.name, name, connection_type='flow')

            # Check for source attribute (single source component)
            if hasattr(component, 'source') and component.source is not None:
                if hasattr(component.source, 'name') and component.source.name in self.components:
                    graph.add_edge(component.source.name, name, connection_type='flow')

            # Check for control_source attribute
            if hasattr(component, 'control_source') and component.control_source is not None:
                if hasattr(component.control_source, 'name') and component.control_source.name in self.components:
                    graph.add_edge(component.control_source.name, name, connection_type='control')

            # Check for precip_source attribute
            if hasattr(component, 'precip_source') and component.precip_source is not None:
                if hasattr(component.precip_source, 'name') and component.precip_source.name in self.components:
                    graph.add_edge(component.precip_source.name, name, connection_type='data')

            # Check for pet_source attribute
            if hasattr(component, 'pet_source') and component.pet_source is not None:
                if hasattr(component.pet_source, 'name') and component.pet_source.name in self.components:
                    graph.add_edge(component.pet_source.name, name, connection_type='data')

            # Check for temp_source attribute
            if hasattr(component, 'temp_source') and component.temp_source is not None:
                if hasattr(component.temp_source, 'name') and component.temp_source.name in self.components:
                    graph.add_edge(component.temp_source.name, name, connection_type='data')

            # Check for evaporation_component attribute (Reservoir)
            if hasattr(component, 'evaporation_component') and component.evaporation_component is not None:
                if hasattr(component.evaporation_component, 'name') and component.evaporation_component.name in self.components:
                    graph.add_edge(component.evaporation_component.name, name, connection_type='data')

        self.graph = graph
        logger.info(f"Built graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
        return graph

    def compute_execution_order(self) -> List[str]:
        """Compute execution order using topological sort.

        Returns:
            List of component names in execution order

        Raises:
            ValueError: If the graph contains circular dependencies
        """
        if self.graph is None:
            self.build_graph()

        try:
            self.execution_order = list(nx.topological_sort(self.graph))
            logger.info(f"Computed execution order: {self.execution_order}")
            return self.execution_order
        except nx.NetworkXError as e:
            raise ValueError(f"Model contains circular dependencies: {e}")

    def step(self, date: datetime) -> Dict[str, Dict[str, Any]]:
        """Execute one simulation timestep for all components.

        This method:
        1. Gets climate data from ClimateManager (if available)
        2. Executes each component's step() method in topological order
        3. Collects and returns all component outputs

        Args:
            date: Current simulation date

        Returns:
            Dictionary mapping component names to their output dictionaries
        """
        # Prepare global_data with climate information
        global_data = {}
        if self.climate_manager:
            global_data.update(self.climate_manager.get_climate_data(date))

        # Execute components in order
        if not self.execution_order:
            self.compute_execution_order()

        results = {}
        for comp_name in self.execution_order:
            component = self.components[comp_name]
            outputs = component.step(date, global_data)
            results[comp_name] = outputs

        return results

    def visualize(self,
                  output_path: Optional[str] = None,
                  figsize: Optional[tuple] = None,
                  show: bool = True,
                  exclude_global_utilities: bool = True) -> Any:
        """Visualize the model's flow network.

        Creates a visual representation of the model showing components as nodes
        and connections as directed edges. Supports explicit node positioning,
        custom colors, and labels from component meta dictionaries.

        Args:
            output_path: Optional path to save the figure
            figsize: Figure size as (width, height) in inches. If None, uses
                    figure_size from settings or defaults to (12, 8)
            show: Whether to display the figure interactively
            exclude_global_utilities: Whether to exclude global utilities
                                     (PrecipGen, TempGen, Hargreaves) from diagram

        Returns:
            matplotlib figure object
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError(
                "matplotlib is required for visualization. "
                "Install it with: pip install matplotlib"
            )

        if self.graph is None:
            self.build_graph()

        # Determine figure size from settings or parameter
        if figsize is None:
            figsize = (12, 8)

        # Filter out global utilities if requested
        nodes_to_draw = list(self.graph.nodes())
        if exclude_global_utilities:
            global_utility_types = {'PrecipGen', 'TempGen', 'HargreavesET', 'TimeseriesClimate'}
            nodes_to_draw = [
                node for node in nodes_to_draw
                if self.components[node].__class__.__name__ not in global_utility_types
            ]

        # Create subgraph with filtered nodes
        subgraph = self.graph.subgraph(nodes_to_draw)

        fig, ax = plt.subplots(figsize=figsize)

        # Extract node positions from meta dictionaries
        pos = {}
        has_explicit_positions = False
        for node_name in subgraph.nodes():
            component = self.components[node_name]
            # Check if component has meta dictionary with x, y coordinates
            if hasattr(component, 'meta') and component.meta:
                x = component.meta.get('x')
                y = component.meta.get('y')
                if x is not None and y is not None:
                    pos[node_name] = (float(x), float(y))
                    has_explicit_positions = True

        # If not all nodes have explicit positions, use spring layout
        if len(pos) != len(subgraph.nodes()):
            # Use spring layout for nodes without explicit positions
            auto_pos = nx.spring_layout(subgraph, k=2, iterations=50, seed=42)
            for node_name in subgraph.nodes():
                if node_name not in pos:
                    pos[node_name] = auto_pos[node_name]

        # Extract node colors from meta dictionaries
        node_colors = []
        for node_name in subgraph.nodes():
            component = self.components[node_name]
            color = 'lightblue'  # Default color
            if hasattr(component, 'meta') and component.meta:
                color = component.meta.get('color', color)
            node_colors.append(color)

        # Extract node labels from meta dictionaries
        labels = {}
        for node_name in subgraph.nodes():
            component = self.components[node_name]
            label = node_name  # Default to component name
            if hasattr(component, 'meta') and component.meta:
                label = component.meta.get('label', label)
            labels[node_name] = label

        # Draw nodes
        nx.draw_networkx_nodes(
            subgraph, pos,
            node_color=node_colors,
            node_size=3000,
            alpha=0.9,
            edgecolors='black',
            linewidths=2,
            ax=ax
        )

        # Draw edges
        nx.draw_networkx_edges(
            subgraph, pos,
            edge_color='gray',
            arrows=True,
            arrowsize=20,
            arrowstyle='->',
            width=2.0,
            connectionstyle='arc3,rad=0.1',
            alpha=0.7,
            ax=ax
        )

        # Draw labels
        nx.draw_networkx_labels(
            subgraph, pos,
            labels=labels,
            font_size=10,
            font_weight='bold',
            font_family='sans-serif',
            ax=ax
        )

        ax.set_title(f"Model: {self.name}", fontsize=14, fontweight='bold')
        ax.axis('off')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"Saved visualization to {output_path}")

        if show:
            plt.show()
        else:
            plt.close()

        return fig
