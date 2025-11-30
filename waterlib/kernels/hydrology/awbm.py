"""
AWBM - Australian Water Balance Model Kernel.

This module contains the pure computational algorithm for the Australian Water
Balance Model (Boughton, 2004). It is a pure function implementation with no
dependencies on the graph structure.

The AWBM algorithm simulates partial area runoff using three surface stores
with different capacities to represent spatial variability in catchment response,
plus routing stores for surface and baseflow.

References:
    Boughton, W. (2004). The Australian water balance model.
    Environmental Modelling & Software, 19(10), 943-956.
"""

from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class AWBMParams:
    """
    Fixed parameters for AWBM algorithm.

    Attributes:
        c_vec: List of three capacity values [C1, C2, C3] in mm
               Default AWBM2002 values: [7.5, 76.0, 152.0]
        bfi: Baseflow Index, fraction of overflow to baseflow (0-1)
        ks: Surface runoff recession constant (0-1)
        kb: Baseflow recession constant (0-1)
        a1: Partial area fraction for store 1 (default: 0.134)
        a2: Partial area fraction for store 2 (default: 0.433)
    """
    c_vec: List[float]
    bfi: float
    ks: float
    kb: float
    a1: float = 0.134
    a2: float = 0.433


@dataclass
class AWBMState:
    """
    State variables for AWBM algorithm.

    Attributes:
        ss1: Surface store 1 moisture content (mm)
        ss2: Surface store 2 moisture content (mm)
        ss3: Surface store 3 moisture content (mm)
        s_surf: Surface runoff routing store (mm)
        b_base: Baseflow routing store (mm)
    """
    ss1: float = 0.0
    ss2: float = 0.0
    ss3: float = 0.0
    s_surf: float = 0.0
    b_base: float = 0.0


@dataclass
class AWBMInputs:
    """
    Inputs for one AWBM timestep.

    Attributes:
        precip_mm: Precipitation (mm)
        pet_mm: Potential evapotranspiration (mm)
    """
    precip_mm: float
    pet_mm: float


@dataclass
class AWBMOutputs:
    """
    Outputs from one AWBM timestep.

    Attributes:
        runoff_mm: Total runoff depth (mm)
        excess_mm: Overflow from surface stores (mm)
        baseflow_mm: Baseflow component (mm)
        surface_flow_mm: Surface flow component (mm)
    """
    runoff_mm: float
    excess_mm: float
    baseflow_mm: float
    surface_flow_mm: float


def awbm_step(
    inputs: AWBMInputs,
    params: AWBMParams,
    state: AWBMState
) -> Tuple[AWBMState, AWBMOutputs]:
    """
    Execute one timestep of AWBM algorithm.

    Pure function with no side effects. Calculates runoff using the Australian
    Water Balance Model with three surface stores and routing stores for
    baseflow and surface flow.

    Args:
        inputs: Current timestep inputs (precipitation, PET)
        params: Fixed model parameters
        state: Current state variables

    Returns:
        Tuple of (new_state, outputs) where:
            - new_state: Updated state variables
            - outputs: Calculated outputs for this timestep
    """
    # Extract inputs
    P = inputs.precip_mm
    PET = inputs.pet_mm

    # Extract state
    SS1 = state.ss1
    SS2 = state.ss2
    SS3 = state.ss3
    S = state.s_surf
    B = state.b_base

    # Extract parameters
    C1, C2, C3 = params.c_vec[0], params.c_vec[1], params.c_vec[2]
    BFI = params.bfi
    Ks = params.ks
    Kb = params.kb
    A1 = params.a1
    A2 = params.a2
    A3 = 1.0 - A1 - A2

    # --- 1. Calculate Capacities (Scaled by Area Fraction) ---
    Cap1 = A1 * C1
    Cap2 = A2 * C2
    Cap3 = A3 * C3

    # --- 2. Surface Store Calculations ---
    # Distributed P and PET [mm/d]
    P1 = P * A1
    P2 = P * A2
    P3 = P * A3
    PET1 = PET * A1
    PET2 = PET * A2
    PET3 = PET * A3

    # Net input to each store (after ET)
    Qin1 = max(P1 - PET1, 0.0)
    Qin2 = max(P2 - PET2, 0.0)
    Qin3 = max(P3 - PET3, 0.0)

    # Overflow from each store
    O1 = max((SS1 + Qin1) - Cap1, 0.0)
    O2 = max((SS2 + Qin2) - Cap2, 0.0)
    O3 = max((SS3 + Qin3) - Cap3, 0.0)

    # Update surface stores
    SS1_new = max(SS1 + (P1 - PET1 - O1), 0.0)
    SS2_new = max(SS2 + (P2 - PET2 - O2), 0.0)
    SS3_new = max(SS3 + (P3 - PET3 - O3), 0.0)

    # Total overflow
    Qover = O1 + O2 + O3

    # --- 3. Flow Splitting ---
    Qi_Base = Qover * BFI
    Qi_Surf = Qover - Qi_Base

    # --- 4. Routing Store Calculations ---
    # Using linear recession
    if B > 0.05:
        Qo_Base = (1.0 - Kb) * B
    else:
        Qo_Base = max(B, 0.0)

    if S > 0.05:
        Qo_Surf = (1.0 - Ks) * S
    else:
        Qo_Surf = max(S, 0.0)

    # Update routing stores
    S_new = max(S + (Qi_Surf - Qo_Surf), 0.0)
    B_new = max(B + (Qi_Base - Qo_Base), 0.0)

    # --- 5. Total Runoff ---
    Runoff = Qo_Surf + Qo_Base

    # --- 6. Package Outputs ---
    new_state = AWBMState(
        ss1=SS1_new,
        ss2=SS2_new,
        ss3=SS3_new,
        s_surf=S_new,
        b_base=B_new
    )

    outputs = AWBMOutputs(
        runoff_mm=Runoff,
        excess_mm=Qover,
        baseflow_mm=Qo_Base,
        surface_flow_mm=Qo_Surf
    )

    return new_state, outputs
