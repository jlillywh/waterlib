"""
RiverDiversion component for waterlib.

This module provides the RiverDiversion component which models flow diversion
from a river or stream with priority-based allocation, demands, and instream
flow requirements.
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from waterlib.core.base import Component
from waterlib.core.exceptions import ConfigurationError


class OutflowSpec(BaseModel):
    """Configuration for individual outflow destination."""
    name: str = Field(
        ...,
        description="Name of the outflow destination"
    )
    priority: int = Field(
        ...,
        ge=1,
        description="Priority level (lower number = higher priority)"
    )
    demand: float = Field(
        ...,
        ge=0,
        description="Water demand in m³/day"
    )


class RiverDiversionConfig(BaseModel):
    """Pydantic configuration model for RiverDiversion component.

    Validates parameters for priority-based river flow diversion.
    """
    max_diversion: float = Field(
        ...,
        ge=0,
        description="Maximum total diversion rate in m³/day"
    )
    instream_flow: float = Field(
        default=0.0,
        ge=0,
        description="Minimum flow that must remain in river in m³/day"
    )
    outflows: Optional[List[OutflowSpec]] = Field(
        default=None,
        description="List of outflow destinations with priority and demand"
    )


class RiverDiversion(Component):
    """Priority-based flow diversion component for rivers or streams.

    The RiverDiversion component models a diversion structure that allocates water
    to multiple destinations based on priority order. It supports:
    - Instream flow requirements (environmental flows)
    - Multiple outflows with individual priorities and demands
    - Shortage allocation based on priority

    Water is allocated in priority order (lower number = higher priority):
    1. Instream flow requirement is satisfied first
    2. Remaining flow is allocated to outflows by priority
    3. Each outflow receives up to its demand, if available
    4. Unallocated flow continues downstream

    Parameters:
        max_diversion: Maximum total diversion rate in m³/day (required)
        instream_flow: Minimum flow that must remain in river in m³/day (optional, default 0)
        outflows: List of outflow destinations with priority and demand (optional)
                  Format: [{"name": "canal_a", "priority": 1, "demand": 5000},
                          {"name": "canal_b", "priority": 2, "demand": 3000}]
                  Lower priority number = higher priority
                  If not specified, creates single "diverted_flow" output

    Inputs (from connections):
        river_flow: Available river flow in m³/day

    Outputs:
        diverted_flow: Total flow extracted from river in m³/day (always present)
        remaining_flow: Flow continuing downstream in m³/day (always present)
        instream_flow: Flow allocated to instream requirement in m³/day
        outflow_1, outflow_2, ...: Individual outflows if specified
        outflow_1_deficit, outflow_2_deficit, ...: Unmet demand for each outflow

    Example YAML (simple with instream flow):
        river_diversion:
          type: RiverDiversion
          params:
            max_diversion: 10000
            instream_flow: 2000

    Example YAML (priority-based allocation):
        priority_diversion:
          type: RiverDiversion
          params:
            max_diversion: 15000
            instream_flow: 3000
            outflows:
              - name: municipal
                priority: 1
                demand: 5000
              - name: irrigation
                priority: 2
                demand: 8000
              - name: industrial
                priority: 3
                demand: 2000

    Example with connections:
        connections:
          - from: upstream_river.outflow
            to: priority_diversion.river_flow
          - from: priority_diversion.municipal
            to: city_demand.available_supply
          - from: priority_diversion.irrigation
            to: farm_demand.available_supply
    """

    def __init__(self, name: str, **params):
        """Initialize RiverDiversion component.

        Args:
            name: Unique component identifier
            **params: Component parameters

        Raises:
            ConfigurationError: If required parameters are missing or invalid
        """
        super().__init__(name, **params)

        # Validate parameters with Pydantic
        try:
            config = RiverDiversionConfig(**params)
        except Exception as e:
            raise ConfigurationError(
                f"RiverDiversion '{name}' configuration error: {str(e)}"
            )

        # Store validated configuration
        self.max_diversion = config.max_diversion
        self.instream_flow_requirement = config.instream_flow

        # Parse outflow specs and sort by priority
        self.outflow_specs: List[Tuple[str, int, float]] = []  # (name, priority, demand)
        if config.outflows:
            self.outflow_specs = [
                (spec.name, spec.priority, spec.demand)
                for spec in config.outflows
            ]
            # Sort by priority (lower number = higher priority)
            self.outflow_specs.sort(key=lambda x: x[1])

        # Initialize outputs
        self.outputs['diverted_flow'] = 0.0
        self.outputs['remaining_flow'] = 0.0
        self.outputs['instream_flow'] = 0.0

        # Initialize individual outflow outputs and deficits
        for outflow_name, _, _ in self.outflow_specs:
            self.outputs[outflow_name] = 0.0
            self.outputs[f'{outflow_name}_deficit'] = 0.0

    def step(self, date: datetime, global_data: dict) -> dict:
        """Execute one timestep of priority-based diversion operation.

        This method implements priority-based water allocation:
        1. Gets available river flow
        2. Allocates flow to instream requirement (highest priority)
        3. Allocates remaining flow to outflows by priority order
        4. Each outflow receives up to its demand
        5. Tracks deficits for unmet demands
        6. Remaining flow continues downstream

        Args:
            date: Current simulation date
            global_data: Dictionary containing global utilities data

        Returns:
            Dictionary of output values for this timestep
        """
        # Get available river flow (default to 0 if not connected)
        river_flow = float(self.inputs.get('river_flow', 0.0))

        # Ensure river flow is non-negative
        river_flow = max(0.0, river_flow)

        # Start with available flow
        available_flow = river_flow

        # Step 1: Allocate to instream flow requirement (highest priority)
        instream_allocated = min(available_flow, self.instream_flow_requirement)
        available_flow -= instream_allocated

        # Step 2: Calculate maximum divertible flow (cannot exceed max_diversion)
        max_divertible = min(available_flow, self.max_diversion)
        available_for_outflows = max_divertible

        # Step 3: Allocate to outflows by priority order
        total_diverted = 0.0
        if self.outflow_specs:
            # Priority-based allocation to specific outflows
            for outflow_name, priority, demand in self.outflow_specs:
                # Allocate up to demand, limited by available flow
                allocated = min(available_for_outflows, demand)
                deficit = demand - allocated

                # Update outputs
                self.outputs[outflow_name] = allocated
                self.outputs[f'{outflow_name}_deficit'] = deficit

                # Update tracking
                total_diverted += allocated
                available_for_outflows -= allocated
        else:
            # No specific outflows - divert up to max_diversion
            total_diverted = max_divertible

        # Step 4: Calculate final flows
        remaining_flow = river_flow - instream_allocated - total_diverted

        # Update summary outputs
        self.outputs['diverted_flow'] = total_diverted
        self.outputs['remaining_flow'] = remaining_flow
        self.outputs['instream_flow'] = instream_allocated

        return self.outputs.copy()
