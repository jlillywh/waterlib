"""
YAML loader and graph construction for waterlib.

This module provides functionality to load water models from YAML configuration
files and construct the internal graph representation used for simulation.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple
import networkx as nx

from waterlib.core.base import Component
from waterlib.core.exceptions import (
    YAMLSyntaxError,
    ConfigurationError,
    CircularDependencyError,
    UndefinedComponentError,
    InvalidConnectionError,
)
from waterlib.core.validation import validate_date_format, validate_date_range
from waterlib.core.config import ModelSettings, ClimateSettings
import logging

logger = logging.getLogger(__name__)


def load_yaml(yaml_path: str) -> Dict[str, Any]:
    """Load and validate YAML file structure.

    This function reads a YAML configuration file and performs basic validation
    to ensure it has the expected structure for a waterlib model.

    Args:
        yaml_path: Path to the YAML configuration file

    Returns:
        Dictionary containing the parsed YAML configuration

    Raises:
        YAMLSyntaxError: If the YAML file has syntax errors or cannot be parsed
        ConfigurationError: If the YAML structure is invalid (missing 'components' key)
        FileNotFoundError: If the YAML file does not exist
    """
    yaml_path = Path(yaml_path)

    # Check if file exists
    if not yaml_path.exists():
        raise FileNotFoundError(f"YAML configuration file not found: {yaml_path}")

    # Load YAML file
    try:
        with open(yaml_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise YAMLSyntaxError(
            f"Failed to parse YAML file '{yaml_path}': {str(e)}"
        )
    except Exception as e:
        raise YAMLSyntaxError(
            f"Error reading YAML file '{yaml_path}': {str(e)}"
        )

    # Validate basic structure
    if config is None:
        raise ConfigurationError(
            f"YAML file '{yaml_path}' is empty or contains only comments"
        )

    if not isinstance(config, dict):
        raise ConfigurationError(
            f"YAML file '{yaml_path}' must contain a dictionary at the top level"
        )

    if 'components' not in config:
        raise ConfigurationError(
            f"YAML file '{yaml_path}' must contain a 'components' key defining model components"
        )

    if not isinstance(config['components'], dict):
        raise ConfigurationError(
            f"'components' in YAML file '{yaml_path}' must be a dictionary"
        )

    if len(config['components']) == 0:
        raise ConfigurationError(
            f"'components' in YAML file '{yaml_path}' is empty - at least one component is required"
        )

    return config


def create_component(name: str, component_config: Dict[str, Any],
                     component_registry: Dict[str, type],
                     yaml_dir: Path = None) -> Component:
    """Factory function to instantiate components from YAML parameters.

    This function creates a component instance based on the 'type' specified
    in the YAML configuration and passes all other parameters to the component's
    __init__ method.

    Args:
        name: Unique component identifier
        component_config: Dictionary of component parameters from YAML
        component_registry: Dictionary mapping type strings to component classes
        yaml_dir: Directory containing the YAML file (for resolving relative paths)

    Returns:
        Instantiated component object

    Raises:
        ConfigurationError: If component type is missing, unknown, or if
                          required parameters are missing
    """
    # Validate that 'type' parameter exists
    if 'type' not in component_config:
        raise ConfigurationError(
            f"Component '{name}' is missing required 'type' parameter"
        )

    component_type = component_config['type']

    # Validate that component type is registered
    if component_type not in component_registry:
        available_types = ', '.join(sorted(component_registry.keys()))
        raise ConfigurationError(
            f"Component '{name}' has unknown type '{component_type}'. "
            f"Available types: {available_types}"
        )

    # Get component class
    component_class = component_registry[component_type]

    # Extract parameters (everything except 'type' and 'meta')
    params = {k: v for k, v in component_config.items() if k not in ('type', 'meta')}

    # Extract meta dictionary if present
    meta = component_config.get('meta', {})

    # Add yaml_dir to params if provided (for components that need to resolve file paths)
    if yaml_dir is not None:
        params['_yaml_dir'] = yaml_dir

    # Instantiate component
    try:
        component = component_class(name=name, meta=meta, **params)
    except TypeError as e:
        # This catches missing required parameters or invalid parameter names
        error_msg = str(e)

        # Special handling for LaggedValue missing initial_value
        if component_type == 'LaggedValue' and 'initial_value' in error_msg:
            raise ConfigurationError(
                f"Component '{name}' of type 'LaggedValue' is missing required parameter 'initial_value'. "
                f"LaggedValue requires 'initial_value' parameter to seed the feedback loop at t=0."
            )

        raise ConfigurationError(
            f"Failed to create component '{name}' of type '{component_type}': {error_msg}"
        )
    except Exception as e:
        # Catch any other errors during component initialization
        raise ConfigurationError(
            f"Error initializing component '{name}' of type '{component_type}': {str(e)}"
        )

    return component


def instantiate_components(config: Dict[str, Any],
                          component_registry: Dict[str, type],
                          yaml_dir: Path = None) -> Dict[str, Component]:
    """Instantiate all components from YAML configuration.

    This function creates instances of all components defined in the YAML
    configuration file using the component factory.

    Args:
        config: Parsed YAML configuration dictionary
        component_registry: Dictionary mapping type strings to component classes
        yaml_dir: Directory containing the YAML file (for resolving relative paths)

    Returns:
        Dictionary mapping component names to component instances

    Raises:
        ConfigurationError: If any component cannot be instantiated
    """
    components = {}

    for name, component_config in config['components'].items():
        # Pass yaml_dir to component factory for path resolution
        components[name] = create_component(name, component_config, component_registry, yaml_dir=yaml_dir)

    return components


def parse_dot_notation(connection_str: str, components: Dict[str, Component]) -> Tuple[Component, str]:
    """Parse dot-notation connection string (e.g., 'component.output').

    This function parses explicit output connections using dot notation and
    returns a tuple of (component_reference, output_name).

    Args:
        connection_str: Connection string, either 'component_name' or 'component_name.output_name'
        components: Dictionary of all component instances

    Returns:
        Tuple of (component_reference, output_name or None)

    Raises:
        UndefinedComponentError: If the referenced component doesn't exist
        ConfigurationError: If the dot-notation format is invalid
    """
    # Validate dot-notation format
    if '..' in connection_str:
        raise ConfigurationError(
            f"Invalid dot-notation format '{connection_str}'. "
            f"Expected format: 'component_name.output_name' or 'component_name'"
        )

    if connection_str.startswith('.') or connection_str.endswith('.'):
        raise ConfigurationError(
            f"Invalid dot-notation format '{connection_str}'. "
            f"Expected format: 'component_name.output_name' or 'component_name'"
        )

    if '.' in connection_str:
        # Explicit output connection: "component.output"
        parts = connection_str.split('.', 1)
        component_name = parts[0]
        output_name = parts[1]

        # Validate output name is not empty
        if not output_name:
            raise ConfigurationError(
                f"Invalid dot-notation format '{connection_str}'. "
                f"Output name cannot be empty. Expected format: 'component_name.output_name'"
            )
    else:
        # Simple component reference: "component"
        component_name = connection_str
        output_name = None

    # Validate component exists
    if component_name not in components:
        available = ', '.join(sorted(components.keys()))
        raise UndefinedComponentError(
            f"Connection references undefined component '{component_name}'. "
            f"Available components: {available}"
        )

    return components[component_name], output_name


def build_graph(config: Dict[str, Any],
                components: Dict[str, Component]) -> nx.DiGraph:
    """Build networkx directed graph from component connections.

    This function creates a directed graph where nodes represent components
    and edges represent dependencies (flow and control connections). The graph
    is used to determine execution order via topological sort.

    Edges are marked with an 'is_feedback' attribute:
    - is_feedback=True: Weak edges targeting LaggedValue components (excluded from topological sort)
    - is_feedback=False: Strong edges representing physical dependencies (used for topological sort)

    Args:
        config: Parsed YAML configuration dictionary
        components: Dictionary of instantiated component instances

    Returns:
        networkx.DiGraph with components as nodes and connections as edges

    Raises:
        UndefinedComponentError: If a connection references a non-existent component
        ConfigurationError: If connection parameters have invalid format
    """
    graph = nx.DiGraph()

    # Add all components as nodes
    for name, component in components.items():
        graph.add_node(
            name,
            component=component,
            type=component.__class__.__name__
        )

    # Parse connections and add edges
    for name, component_config in config['components'].items():
        component = components[name]

        # Check if this component is a LaggedValue (target of weak edges)
        is_target_lagged = component.__class__.__name__ == 'LaggedValue'

        # Process 'inflows' connections (flow connections)
        if 'inflows' in component_config:
            inflows = component_config['inflows']

            # Validate inflows is a list
            if not isinstance(inflows, list):
                raise ConfigurationError(
                    f"Component '{name}': 'inflows' must be a list, got {type(inflows).__name__}"
                )

            # Parse each inflow connection
            inflow_getters = []
            for inflow_str in inflows:
                if not isinstance(inflow_str, str):
                    raise ConfigurationError(
                        f"Component '{name}': inflow connection must be a string, "
                        f"got {type(inflow_str).__name__}"
                    )

                source_component, output_name = parse_dot_notation(inflow_str, components)
                inflow_getters.append((source_component, output_name))

                # Add edge: source -> consumer
                # Mark as feedback if target (consumer) is LaggedValue
                graph.add_edge(
                    source_component.name,
                    name,
                    connection_type='flow',
                    parameter='inflows',
                    is_feedback=is_target_lagged
                )

            # Store inflow_getters on component for use during simulation
            # This allows Junction and other components to retrieve specific outputs
            component.inflow_getters = inflow_getters

        # Process 'source' connection (flow connection for DemandNode)
        if 'source' in component_config:
            source_str = component_config['source']

            if not isinstance(source_str, str):
                raise ConfigurationError(
                    f"Component '{name}': 'source' must be a string, "
                    f"got {type(source_str).__name__}"
                )

            source_component, output_name = parse_dot_notation(source_str, components)

            # Store source reference on component
            component.source = source_component

            # Add edge: source -> consumer
            # Mark as feedback if target (consumer) is LaggedValue
            graph.add_edge(
                source_component.name,
                name,
                connection_type='flow',
                parameter='source',
                is_feedback=is_target_lagged
            )

        # Process 'control_source' connection (control connection for Weir)
        if 'control_source' in component_config:
            control_str = component_config['control_source']

            if not isinstance(control_str, str):
                raise ConfigurationError(
                    f"Component '{name}': 'control_source' must be a string, "
                    f"got {type(control_str).__name__}"
                )

            control_component, output_name = parse_dot_notation(control_str, components)

            # Store control_source reference on component
            component.control_source = control_component

            # Add edge: controller -> controlled
            # Mark as feedback if target (controlled) is LaggedValue
            graph.add_edge(
                control_component.name,
                name,
                connection_type='control',
                parameter='control_source',
                is_feedback=is_target_lagged
            )

        # Process 'precip_source' connection (flow connection for RunoffCoefficient and AWBM)
        # Note: Snow17 precip_source is handled in the resolution section below
        if 'precip_source' in component_config and component.__class__.__name__ != 'Snow17':
            precip_str = component_config['precip_source']

            if not isinstance(precip_str, str):
                raise ConfigurationError(
                    f"Component '{name}': 'precip_source' must be a string, "
                    f"got {type(precip_str).__name__}"
                )

            precip_component, output_name = parse_dot_notation(precip_str, components)

            # Store precip_source reference and output name on component
            component.precip_source = precip_component
            component.precip_output = output_name

            # Add edge: source -> consumer
            # Mark as feedback if target (consumer) is LaggedValue
            graph.add_edge(
                precip_component.name,
                name,
                connection_type='flow',
                parameter='precip_source',
                is_feedback=is_target_lagged
            )

        # Process 'pet_source' connection (flow connection for AWBM)
        if 'pet_source' in component_config:
            pet_str = component_config['pet_source']

            if not isinstance(pet_str, str):
                raise ConfigurationError(
                    f"Component '{name}': 'pet_source' must be a string, "
                    f"got {type(pet_str).__name__}"
                )

            pet_component, output_name = parse_dot_notation(pet_str, components)

            # Store pet_source reference and output name on component
            component.pet_source = pet_component
            component.pet_output = output_name

            # Add edge: source -> consumer
            # Mark as feedback if target (consumer) is LaggedValue
            graph.add_edge(
                pet_component.name,
                name,
                connection_type='flow',
                parameter='pet_source',
                is_feedback=is_target_lagged
            )

        # Note: Snow17 temp_source is handled in the resolution section below

    # Resolve source references for LaggedValue components
    # This must happen after graph construction so all components exist
    for component in components.values():
        if component.__class__.__name__ == 'LaggedValue':
            # Parse the source string to get component and output references
            source_component, output_name = parse_dot_notation(
                component._source_string,
                components
            )
            # Store resolved references on the LaggedValue instance
            component._source_component = source_component
            component._source_output = output_name

        # Resolve temperature and precipitation sources for Snow17 components
        elif component.__class__.__name__ == 'Snow17':
            # Parse temp_source
            temp_component, temp_output = parse_dot_notation(
                component.temp_source_str,
                components
            )
            # Parse precip_source
            precip_component, precip_output = parse_dot_notation(
                component.precip_source_str,
                components
            )
            # Store resolved references
            component.temp_source = temp_component
            component.temp_output = temp_output
            component.precip_source = precip_component
            component.precip_output = precip_output

            # Add edges for sources (already added in earlier processing, but ensure they exist)
            if not graph.has_edge(temp_component.name, component.name):
                graph.add_edge(
                    temp_component.name,
                    component.name,
                    connection_type='data',
                    parameter='temp_source',
                    is_feedback=False
                )
            if not graph.has_edge(precip_component.name, component.name):
                graph.add_edge(
                    precip_component.name,
                    component.name,
                    connection_type='data',
                    parameter='precip_source',
                    is_feedback=False
                )

        # Resolve temperature sources for HargreavesET components
        elif component.__class__.__name__ == 'HargreavesET':
            # Parse tmin_source
            tmin_component, tmin_output = parse_dot_notation(
                component.tmin_source_str,
                components
            )
            # Parse tmax_source
            tmax_component, tmax_output = parse_dot_notation(
                component.tmax_source_str,
                components
            )
            # Inject resolved references
            component.set_sources(tmin_component, tmin_output, tmax_component, tmax_output)

            # Add edges for temperature sources
            graph.add_edge(
                tmin_component.name,
                component.name,
                connection_type='data',
                parameter='tmin_source',
                is_feedback=False
            )
            graph.add_edge(
                tmax_component.name,
                component.name,
                connection_type='data',
                parameter='tmax_source',
                is_feedback=False
            )

        # Resolve evaporation source for Reservoir components (if configured)
        elif component.__class__.__name__ == 'Reservoir' and hasattr(component, 'evaporation_source_str') and component.evaporation_source_str:
            # Parse evaporation_source
            evap_component, evap_output = parse_dot_notation(
                component.evaporation_source_str,
                components
            )
            # Store resolved references
            component.evaporation_component = evap_component
            component.evaporation_output = evap_output

            # Add edge for evaporation source
            graph.add_edge(
                evap_component.name,
                component.name,
                connection_type='data',
                parameter='evaporation_source',
                is_feedback=False
            )

    return graph


def compute_execution_order(graph: nx.DiGraph) -> List[str]:
    """Compute execution order using topological sort on strong edges only.

    This function creates a temporary graph view excluding weak edges (is_feedback=True)
    to enable topological sorting despite cycles in the full graph. Weak edges represent
    information links using lagged values and are excluded from execution ordering.

    Args:
        graph: Directed graph of component connections

    Returns:
        List of component names in execution order

    Raises:
        CircularDependencyError: If the graph contains unbreakable cycles (cycles in strong edges)
    """
    # Create edge filter function that returns True for strong edges only
    def strong_edge_filter(n1, n2):
        edge_data = graph.edges[n1, n2]
        return not edge_data.get('is_feedback', False)

    # Create subgraph view with strong edges only (excludes weak/feedback edges)
    strong_graph = nx.subgraph_view(
        graph,
        filter_edge=strong_edge_filter
    )

    try:
        # Compute topological sort on the acyclic strong edge graph
        execution_order = list(nx.topological_sort(strong_graph))
        return execution_order
    except (nx.NetworkXError, nx.NetworkXUnfeasible, RuntimeError) as e:
        # Even with weak edges removed, cycles exist - these are unbreakable
        # NetworkX can raise NetworkXError, NetworkXUnfeasible, or RuntimeError for cycles
        try:
            cycles = list(nx.simple_cycles(strong_graph))

            if cycles:
                # Format cycle information for error message
                cycle_strs = []
                for cycle in cycles:
                    cycle_str = ' -> '.join(cycle + [cycle[0]])
                    cycle_strs.append(cycle_str)

                cycles_formatted = '\n  '.join(cycle_strs)
                raise CircularDependencyError(
                    f"Model contains circular dependencies that cannot be broken by LaggedValue components:\n"
                    f"  {cycles_formatted}\n\n"
                    f"Add a LaggedValue component to break the cycle."
                )
            else:
                # Shouldn't happen, but handle gracefully
                raise CircularDependencyError(
                    "Model contains circular dependencies (cycles could not be identified). "
                    "Consider using LaggedValue components to break feedback loops."
                )
        except Exception as e:
            if isinstance(e, CircularDependencyError):
                raise
            # If cycle detection fails for some reason, raise generic error
            raise CircularDependencyError(
                f"Model contains circular dependencies: {str(e)}. "
                f"Consider using LaggedValue components to break feedback loops."
            )


def validate_settings(settings: Dict[str, Any]) -> ModelSettings:
    """Validate model settings and return ModelSettings dataclass.

    Args:
        settings: Settings dictionary from YAML

    Returns:
        ModelSettings instance with validated settings

    Raises:
        ConfigurationError: If settings are invalid or missing required fields
    """
    # Check for required settings block
    if not settings:
        raise ConfigurationError(
            "Missing required 'settings' block in model.yaml. "
            "The settings block must contain at least 'start_date' and 'end_date'."
        )

    # Check for required fields
    if 'start_date' not in settings:
        raise ConfigurationError(
            "Missing required setting: 'start_date'. "
            "The settings block must contain a 'start_date' in YYYY-MM-DD format."
        )

    if 'end_date' not in settings:
        raise ConfigurationError(
            "Missing required setting: 'end_date'. "
            "The settings block must contain an 'end_date' in YYYY-MM-DD format."
        )

    # Parse and validate settings using ModelSettings dataclass
    try:
        model_settings = ModelSettings.from_dict(settings)
        return model_settings
    except ValueError as e:
        # Convert ValueError to ConfigurationError for consistency
        raise ConfigurationError(str(e))
    except Exception as e:
        raise ConfigurationError(f"Error parsing settings: {str(e)}")


def _register_data_connections(model):
    """Extract and register formal data connections from component attributes.

    This function analyzes component attributes (inflow_getters, source) and
    populates model.data_connections with explicit (source, output, target, input)
    tuples. This provides a formal record of all data dependencies.

    Args:
        model: Model instance with instantiated components

    Note:
        Currently, most connections are handled implicitly via _transfer_data()
        reading component attributes. This function creates an explicit registry
        for future use (e.g., debugging, visualization, optimization).
    """
    data_connections = []

    for comp_name, component in model.components.items():
        # Handle 'inflows' connections
        if hasattr(component, 'inflow_getters') and component.inflow_getters:
            for idx, (source_comp, output_name) in enumerate(component.inflow_getters, 1):
                # Register: (source_comp, output_name, target_comp, input_name)
                input_name = f'inflow_{idx}'
                data_connections.append((source_comp, output_name, component, input_name))

        # Handle 'source' connections
        if hasattr(component, 'source') and component.source is not None:
            source_comp = component.source
            # Demand expects 'available_supply', source provides 'outflow'
            # (or fallback to 'release' or 'storage')
            output_name = 'outflow'  # Primary output to check
            input_name = 'available_supply'
            data_connections.append((source_comp, output_name, component, input_name))

    model.data_connections = data_connections
    logger.info(f"Registered {len(data_connections)} formal data connections")


def load_model(yaml_path: str, validate: bool = True):
    """Load and initialize a water model from a YAML configuration file.

    This is the main entry point for creating a Model instance following the
    simplified library-first design. It performs the following steps:
    1. Load and validate the YAML file
    2. Extract model metadata (name, description)
    3. Extract settings (dates, climate, visualization)
    4. Instantiate all components using the component factory
    5. Extract connections
    6. Return a Model instance ready for simulation

    Args:
        yaml_path: Path to the YAML configuration file
        validate: Whether to perform validation after loading (default: True)

    Returns:
        Model instance with components, connections, and settings

    Raises:
        FileNotFoundError: If the YAML file doesn't exist
        YAMLSyntaxError: If the YAML file has syntax errors
        ConfigurationError: If the configuration is invalid
        UndefinedComponentError: If a connection references a non-existent component

    Example:
        >>> from waterlib.core.loader import load_model
        >>> model = load_model('examples/simple_model.yaml')
        >>> print(f"Model: {model.name}")
        >>> print(f"Components: {list(model.components.keys())}")
        >>> print(f"Settings: {model.settings}")
    """
    # Import here to avoid circular imports
    from waterlib.core.simple_model import Model
    from waterlib.components import get_component_registry

    logger.info(f"Loading model from {yaml_path}")

    # Step 1: Load and validate YAML
    config = load_yaml(yaml_path)

    # Get YAML directory for resolving relative paths
    yaml_dir = Path(yaml_path).parent

    # Get component registry
    component_registry = get_component_registry()

    # Step 2: Extract model metadata
    name = config.get('name', 'Unnamed Model')
    description = config.get('description', '')

    # Step 3: Extract and validate settings
    settings_dict = config.get('settings', {})

    try:
        model_settings = validate_settings(settings_dict)
        logger.info(f"Settings validated: {model_settings.start_date} to {model_settings.end_date}")
    except ConfigurationError as e:
        logger.error(f"Settings validation failed: {str(e)}")
        raise

    # Step 4: Instantiate all components
    try:
        components = instantiate_components(config, component_registry, yaml_dir)
        logger.info(f"Instantiated {len(components)} components")
    except ConfigurationError as e:
        logger.error(f"Component instantiation failed: {str(e)}")
        raise

    # Step 5: Build graph to parse inline connections and resolve component references
    try:
        graph = build_graph(config, components)
        logger.info(f"Built graph with {len(components)} nodes and {graph.number_of_edges()} edges")
    except (UndefinedComponentError, ConfigurationError) as e:
        logger.error(f"Graph building failed: {str(e)}")
        raise

    # Step 6: Extract explicit connections list (if any)
    connections = config.get('connections', [])

    # Step 7: Create Model instance
    model = Model(
        name=name,
        description=description,
        components=components,
        connections=connections,
        settings=model_settings,
        yaml_dir=yaml_dir
    )

    # Step 7.5: Extract and register data connections from component attributes
    # This populates model.data_connections for explicit tracking
    _register_data_connections(model)

    # Step 8: Perform validation if requested
    if validate:
        try:
            from waterlib.core.validation import ModelValidator
            validator = ModelValidator(model)
            validator.validate(raise_on_error=True)
            logger.info("Model validation passed")
        except Exception as e:
            logger.error(f"Model validation failed: {str(e)}")
            raise

    return model
