"""
Global climate utilities for waterlib.

This module provides climate data generation and calculation utilities that are
available globally to all components without requiring explicit YAML component
definitions. These utilities include:

- PrecipGen: Stochastic daily precipitation generator
- TempGen: Stochastic daily temperature (min/max) generator
- StochasticClimate: WGEN weather generator for precipitation, temperature, and solar radiation
- Hargreaves-Samani ET calculation function

Climate utilities can operate in two modes:
1. Stochastic mode: Generate synthetic time series using statistical parameters
2. Timeseries mode: Load actual data from CSV files
"""

import math
import random
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
import logging

import pandas as pd
import numpy as np

from waterlib.core.exceptions import ConfigurationError
from waterlib.kernels.climate.et import hargreaves_et, HargreavesETParams, HargreavesETInputs


logger = logging.getLogger(__name__)


# ============================================================================
# WGEN Data Models
# ============================================================================

@dataclass
class MonthlyParams:
    """Monthly WGEN parameters.

    Attributes:
        month: Month number (1-12)
        p_wet_wet: Probability of wet day following wet day [0-1]
        p_wet_dry: Probability of wet day following dry day [0-1]
        alpha: Gamma distribution shape parameter (dimensionless)
        beta: Gamma distribution scale parameter [mm]
    """
    month: int
    p_wet_wet: float
    p_wet_dry: float
    alpha: float
    beta: float

    def __post_init__(self):
        """Validate parameter values."""
        if not 1 <= self.month <= 12:
            raise ValueError(f"Month must be between 1 and 12, got {self.month}")
        if not 0 <= self.p_wet_wet <= 1:
            raise ValueError(
                f"p_wet_wet must be between 0 and 1, got {self.p_wet_wet} for month {self.month}"
            )
        if not 0 <= self.p_wet_dry <= 1:
            raise ValueError(
                f"p_wet_dry must be between 0 and 1, got {self.p_wet_dry} for month {self.month}"
            )
        if self.alpha <= 0:
            raise ValueError(
                f"alpha must be > 0, got {self.alpha} for month {self.month}"
            )
        if self.beta <= 0:
            raise ValueError(
                f"beta must be > 0, got {self.beta} for month {self.month}"
            )


@dataclass
class StationConstants:
    """Scalar station constants for WGEN.

    All temperature parameters are input in Celsius and converted to Kelvin internally.

    Attributes:
        latitude: Station latitude [degrees]
        elevation_m: Station elevation [meters]
        txmd: Mean Tmax dry [°C]
        txmw: Mean Tmax wet [°C]
        tn: Mean Tmin [°C]
        atx: Amplitude Tmax [°C]
        atn: Amplitude Tmin [°C]
        cvtx: CV Tmax mean
        acvtx: CV Tmax amplitude
        cvtn: CV Tmin mean
        acvtn: CV Tmin amplitude
        dt_day: Peak temperature day of year
        rs_mean: Mean solar radiation [MJ/m²/day]
        rs_amplitude: Solar radiation amplitude [MJ/m²/day]
        rs_cv: Solar radiation coefficient of variation
        rs_wet_factor: Solar radiation reduction factor for wet days
        min_rain_mm: Minimum precipitation threshold [mm]
    """
    latitude: float
    elevation_m: float
    txmd: float
    txmw: float
    tn: float
    atx: float
    atn: float
    cvtx: float
    acvtx: float
    cvtn: float
    acvtn: float
    dt_day: int
    rs_mean: float = 15.0
    rs_amplitude: float = 10.0
    rs_cv: float = 0.3
    rs_wet_factor: float = 0.7
    min_rain_mm: float = 0.254

    def __post_init__(self):
        """Validate parameter values."""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"latitude must be between -90 and 90, got {self.latitude}")
        if self.elevation_m < 0:
            raise ValueError(f"elevation_m must be >= 0, got {self.elevation_m}")
        if self.cvtx < 0:
            raise ValueError(f"cvtx must be >= 0, got {self.cvtx}")
        if self.cvtn < 0:
            raise ValueError(f"cvtn must be >= 0, got {self.cvtn}")
        if self.rs_cv < 0:
            raise ValueError(f"rs_cv must be >= 0, got {self.rs_cv}")
        if not 1 <= self.dt_day <= 366:
            raise ValueError(f"dt_day must be between 1 and 366, got {self.dt_day}")
        if self.min_rain_mm < 0:
            raise ValueError(f"min_rain_mm must be >= 0, got {self.min_rain_mm}")
        if not 0 <= self.rs_wet_factor <= 1:
            raise ValueError(f"rs_wet_factor must be between 0 and 1, got {self.rs_wet_factor}")


@dataclass
class WgenState:
    """Internal state maintained between timesteps.

    Attributes:
        wet: Previous day wet/dry status
        x: Fourier coefficients (3-element vector)
        rain: Current precipitation [mm]
    """
    wet: bool = False
    x: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rain: float = 0.0


# ============================================================================
# WGEN Parameter Loading
# ============================================================================

def load_wgen_parameters(param_file: Path, yaml_dir: Path) -> Dict[int, MonthlyParams]:
    """Load WGEN monthly parameters from CSV file.

    Args:
        param_file: Path to CSV file (relative or absolute)
        yaml_dir: Directory containing YAML file (for resolving relative paths)

    Returns:
        Dictionary mapping month (1-12) to MonthlyParams

    Raises:
        FileNotFoundError: If CSV file not found
        ConfigurationError: If CSV structure is invalid
        ValueError: If parameter values are out of range
    """
    # Resolve file path
    if not param_file.is_absolute():
        param_file = yaml_dir / param_file

    # Check file exists
    if not param_file.exists():
        raise FileNotFoundError(f"WGEN parameter file not found: {param_file}")

    # Load CSV
    try:
        df = pd.read_csv(param_file, comment='#')
    except Exception as e:
        raise ConfigurationError(
            f"Failed to read WGEN parameter file {param_file}: {str(e)}"
        )

    # Normalize column names to lowercase
    df.columns = df.columns.str.lower()

    # Validate structure
    required_columns = ['month', 'pww', 'pwd', 'alpha', 'beta']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ConfigurationError(
            f"WGEN parameter file missing required columns: {missing_columns}. "
            f"Found columns: {list(df.columns)}"
        )

    # Validate row count
    if len(df) != 12:
        raise ConfigurationError(
            f"WGEN parameter file must have exactly 12 rows (one per month), found {len(df)}"
        )

    # Parse parameters
    params = {}
    for _, row in df.iterrows():
        try:
            month_params = MonthlyParams(
                month=int(row['month']),
                p_wet_wet=float(row['pww']),
                p_wet_dry=float(row['pwd']),
                alpha=float(row['alpha']),
                beta=float(row['beta'])
            )
            params[month_params.month] = month_params
        except ValueError as e:
            raise ValueError(f"Invalid parameter value in WGEN CSV: {str(e)}")

    # Validate all months present
    for month in range(1, 13):
        if month not in params:
            raise ConfigurationError(
                f"WGEN parameter file missing month {month}"
            )

    logger.info(f"Loaded WGEN parameters from {param_file}")
    return params


def parse_wgen_config(config: Dict[str, Any]) -> StationConstants:
    """Parse WGEN configuration from YAML settings.

    Args:
        config: Dictionary containing WGEN configuration

    Returns:
        StationConstants with validated parameters

    Raises:
        ConfigurationError: If required parameters are missing
        ValueError: If parameter values are out of range
    """
    # Required parameters
    required_params = [
        'latitude', 'elevation_m', 'txmd', 'txmw', 'tn', 'atx', 'atn',
        'cvtx', 'acvtx', 'cvtn', 'acvtn', 'dt_day'
    ]

    missing_params = [p for p in required_params if p not in config]
    if missing_params:
        raise ConfigurationError(
            f"WGEN configuration missing required parameters: {missing_params}"
        )

    # Extract parameters with defaults for optional ones
    try:
        constants = StationConstants(
            latitude=float(config['latitude']),
            elevation_m=float(config['elevation_m']),
            txmd=float(config['txmd']),
            txmw=float(config['txmw']),
            tn=float(config['tn']),
            atx=float(config['atx']),
            atn=float(config['atn']),
            cvtx=float(config['cvtx']),
            acvtx=float(config['acvtx']),
            cvtn=float(config['cvtn']),
            acvtn=float(config['acvtn']),
            dt_day=int(config['dt_day']),
            rs_mean=float(config.get('rs_mean', 15.0)),
            rs_amplitude=float(config.get('rs_amplitude', 10.0)),
            rs_cv=float(config.get('rs_cv', 0.3)),
            rs_wet_factor=float(config.get('rs_wet_factor', 0.7)),
            min_rain_mm=float(config.get('min_rain_mm', 0.254))
        )
    except ValueError as e:
        raise ValueError(f"Invalid WGEN configuration parameter: {str(e)}")

    logger.info(f"Parsed WGEN configuration: latitude={constants.latitude}°, "
                f"elevation={constants.elevation_m}m")
    return constants


# ============================================================================
# WGEN Components
# ============================================================================

class WgenPrecipitation:
    """WGEN precipitation generator using Markov chain-gamma model.

    Generates daily precipitation using a first-order Markov chain for wet/dry
    state transitions and a gamma distribution for precipitation amounts on wet days.

    Attributes:
        monthly_params: Dictionary mapping month (1-12) to MonthlyParams
        min_threshold: Minimum precipitation threshold [mm]
        wet: Current wet/dry state (True = wet, False = dry)
        rain: Current precipitation amount [mm]
        rng: Random number generator (for deterministic mode)
    """

    def __init__(self,
                 monthly_params: Dict[int, MonthlyParams],
                 min_threshold: float = 0.254,
                 deterministic: bool = False,
                 seed: Optional[int] = None):
        """Initialize WGEN precipitation generator.

        Args:
            monthly_params: Dictionary mapping month (1-12) to MonthlyParams
            min_threshold: Minimum precipitation threshold [mm]
            deterministic: If True, use fixed random seed for reproducibility
            seed: Random seed (used if deterministic=True)
        """
        self.monthly_params = monthly_params
        self.min_threshold = min_threshold
        self.deterministic = deterministic

        # Initialize state - start with dry state (Requirement 3.6)
        self.wet = False
        self.rain = 0.0

        # Initialize random number generator
        if deterministic:
            if seed is None:
                seed = 42  # Default seed for deterministic mode
            self.rng = np.random.RandomState(seed)
            logger.warning("WGEN precipitation in deterministic mode - results are not stochastic")
        else:
            self.rng = np.random.RandomState()

        logger.info(f"Initialized WgenPrecipitation: deterministic={deterministic}")

    def generate(self, date: datetime) -> float:
        """Generate precipitation for a single day.

        Uses first-order Markov chain to determine wet/dry state, then
        samples from gamma distribution for wet day amounts.

        Args:
            date: Current simulation date

        Returns:
            Daily precipitation [mm/day]
        """
        # Get month (1-12)
        month = date.month
        params = self.monthly_params[month]

        # Determine wet/dry state using Markov chain (Requirements 3.1, 3.2, 3.3)
        if self.wet:
            # Previous day was wet, use p_wet_wet
            transition_prob = params.p_wet_wet
        else:
            # Previous day was dry, use p_wet_dry
            transition_prob = params.p_wet_dry

        # Generate random number and determine today's state
        is_wet_today = self.rng.random() < transition_prob

        # Generate precipitation amount if wet (Requirement 3.4)
        if is_wet_today:
            # Sample from gamma distribution
            # NumPy uses shape (alpha) and scale (beta) parameterization
            precip = self.rng.gamma(params.alpha, params.beta)

            # Apply minimum threshold (Requirement 3.5)
            if precip < self.min_threshold:
                precip = 0.0
                is_wet_today = False  # Treat as dry if below threshold
        else:
            precip = 0.0

        # Update state for next timestep
        self.wet = is_wet_today
        self.rain = precip

        return precip


class WgenSolarRadiation:
    """WGEN solar radiation generator using Fourier series.

    Generates daily solar radiation using the third element (x[2]) of the
    Fourier harmonic vector from temperature generation, combined with
    seasonal patterns and wet/dry day adjustments.

    Attributes:
        constants: StationConstants with solar radiation parameters
        x: Reference to Fourier coefficient vector (shared with temperature)
        rng: Random number generator (for deterministic mode)
    """

    def __init__(self,
                 constants: StationConstants,
                 x: List[float],
                 deterministic: bool = False,
                 seed: Optional[int] = None):
        """Initialize WGEN solar radiation generator.

        Args:
            constants: StationConstants with solar radiation parameters
            x: Reference to shared Fourier coefficient vector (3 elements)
            deterministic: If True, use fixed random seed for reproducibility
            seed: Random seed (used if deterministic=True)
        """
        self.constants = constants
        self.x = x  # Shared state with temperature component
        self.deterministic = deterministic

        # Initialize random number generator (not currently used, but kept for consistency)
        if deterministic:
            if seed is None:
                seed = 42  # Default seed for deterministic mode
            self.rng = np.random.RandomState(seed)
            logger.warning("WGEN solar radiation in deterministic mode - results are not stochastic")
        else:
            self.rng = np.random.RandomState()

        logger.info(f"Initialized WgenSolarRadiation: deterministic={deterministic}")

    def generate(self, date: datetime, wet: bool) -> float:
        """Generate solar radiation for a single day.

        Uses the third element (x[2]) of the Fourier harmonic vector combined
        with seasonal patterns and wet/dry day adjustments.

        Args:
            date: Current simulation date
            wet: Current wet/dry state (from precipitation generator)

        Returns:
            Daily solar radiation [MJ/m²/day]
        """
        # Get day of year (1-366)
        doy = date.timetuple().tm_yday

        # Calculate seasonal component using Fourier series (Requirements 5.1, 5.2)
        dt = np.cos(0.0172 * (doy - self.constants.dt_day))

        # Mean solar radiation for the day
        rsm = self.constants.rs_mean + self.constants.rs_amplitude * dt

        # Wet/dry day adjustment (Requirements 5.3, 5.4)
        if wet:
            # Wet days: reduce solar radiation to reflect cloud cover
            rsm_adjusted = rsm * self.constants.rs_wet_factor
        else:
            # Dry days: use unadjusted values
            rsm_adjusted = rsm

        # Calculate stochastic component using x[2] from Fourier harmonic
        # x[2] is generated by the temperature component
        solar_rad_raw = self.x[2] * (rsm_adjusted * self.constants.rs_cv) + rsm_adjusted

        # CRITICAL: Enforce non-negativity constraint (Requirement 5.5)
        # x[2] comes from a normal distribution and can be negative enough
        # to produce negative radiation values without this clamp
        solar_rad = max(0.0, solar_rad_raw)

        return solar_rad


class WgenTemperature:
    """WGEN temperature generator using Fourier series with correlation.

    Generates daily minimum and maximum temperatures using a one-term Fourier
    series for seasonal patterns combined with serial and cross-correlation
    for realistic day-to-day variation.

    All calculations are performed in Kelvin internally, with Celsius conversions
    at input/output boundaries.

    Attributes:
        constants: StationConstants with temperature parameters
        wet: Reference to wet/dry state (shared with precipitation)
        x: Fourier coefficient vector (3 elements, shared state)
        rng: Random number generator (for deterministic mode)
    """

    # Serial correlation matrix (A) from Richardson & Wright (1984)
    A_MATRIX = np.array([
        [0.567, 0.086, -0.002],
        [0.253, 0.504, -0.050],
        [-0.006, -0.039, 0.244]
    ])

    # Cross-correlation matrix (B) from Richardson & Wright (1984)
    B_MATRIX = np.array([
        [0.781, 0.000, 0.000],
        [0.328, 0.637, 0.000],
        [0.238, -0.341, 0.873]
    ])

    def __init__(self,
                 constants: StationConstants,
                 x: List[float],
                 deterministic: bool = False,
                 seed: Optional[int] = None):
        """Initialize WGEN temperature generator.

        Args:
            constants: StationConstants with temperature parameters
            x: Reference to shared Fourier coefficient vector (3 elements)
            deterministic: If True, use fixed random seed for reproducibility
            seed: Random seed (used if deterministic=True)
        """
        self.constants = constants
        self.x = x  # Shared state with other components
        self.deterministic = deterministic

        # Initialize random number generator
        if deterministic:
            if seed is None:
                seed = 42  # Default seed for deterministic mode
            self.rng = np.random.RandomState(seed)
            logger.warning("WGEN temperature in deterministic mode - results are not stochastic")
        else:
            self.rng = np.random.RandomState()

        logger.info(f"Initialized WgenTemperature: deterministic={deterministic}")

    def _box_muller_transform(self) -> tuple:
        """Generate two independent standard normal random variables.

        Uses Box-Muller transformation to convert uniform random variables
        to standard normal distribution. Values are clamped to [-2.5, 2.5]
        to avoid extreme outliers that could produce unrealistic temperatures.

        Returns:
            Tuple of (z1, z2) where both are N(0,1) distributed, clamped to [-2.5, 2.5]
        """
        # Generate two uniform random variables
        u1 = self.rng.random()
        u2 = self.rng.random()

        # Avoid log(0) by clamping u1 away from 0
        u1 = max(u1, 1e-10)

        # Box-Muller transformation
        z1 = np.sqrt(-2.0 * np.log(u1)) * np.cos(2.0 * np.pi * u2)
        z2 = np.sqrt(-2.0 * np.log(u1)) * np.sin(2.0 * np.pi * u2)

        # Clamp to avoid extreme outliers (per design document)
        z1 = np.clip(z1, -2.5, 2.5)
        z2 = np.clip(z2, -2.5, 2.5)

        return z1, z2

    def generate(self, date: datetime, wet: bool) -> tuple:
        """Generate minimum and maximum temperature for a single day.

        Uses Fourier series for seasonal component and correlation matrices
        for stochastic variation. Adjusts for wet/dry day effects.

        Args:
            date: Current simulation date
            wet: Current wet/dry state (from precipitation generator)

        Returns:
            Tuple of (tmin, tmax) in °C
        """
        # Get day of year (1-366)
        doy = date.timetuple().tm_yday

        # Convert temperature parameters from Celsius to Kelvin
        txmd_k = self.constants.txmd + 273.15
        txmw_k = self.constants.txmw + 273.15
        tn_k = self.constants.tn + 273.15
        atx_k = self.constants.atx  # Amplitude, no offset needed
        atn_k = self.constants.atn  # Amplitude, no offset needed

        # Calculate seasonal component using Fourier series (Requirement 4.1)
        dt = np.cos(0.0172 * (doy - self.constants.dt_day))

        # Mean temperatures for the day (in Kelvin)
        txm_k = txmd_k + atx_k * dt
        tnm_k = tn_k + atn_k * dt

        # Wet/dry day adjustment (Requirement 4.3)
        if wet:
            # Wet days: lower tmax, higher tmin
            d1 = self.constants.txmd - self.constants.txmw  # In Celsius
            txm_k = txm_k - d1  # Adjust in Kelvin

        # Calculate coefficient of variation for the day
        cv_tx = self.constants.cvtx + self.constants.acvtx * dt
        cv_tn = self.constants.cvtn + self.constants.acvtn * dt

        # Generate three correlated random variables using Box-Muller (Requirement 4.4)
        z1, z2 = self._box_muller_transform()
        z3, _ = self._box_muller_transform()
        e = np.array([z1, z2, z3])

        # Apply serial correlation (A) and cross-correlation (B) matrices (Requirement 4.2)
        x_prev = np.array(self.x)
        x_new = self.A_MATRIX @ x_prev + self.B_MATRIX @ e

        # Update shared state
        self.x[0] = x_new[0]
        self.x[1] = x_new[1]
        self.x[2] = x_new[2]

        # Calculate final temperatures (in Kelvin)
        tmax_k = x_new[0] * (txm_k * cv_tx) + txm_k
        tmin_k = x_new[1] * (tnm_k * cv_tn) + tnm_k

        # Enforce tmax >= tmin constraint (Requirement 4.5)
        if tmax_k < tmin_k:
            tmax_k = tmin_k

        # Convert back to Celsius for output
        tmax_c = tmax_k - 273.15
        tmin_c = tmin_k - 273.15

        return tmin_c, tmax_c


# ============================================================================
# Existing Climate Generators
# ============================================================================

class PrecipGen:
    """Stochastic daily precipitation generator.

    Generates synthetic daily precipitation time series using a simple
    two-state Markov chain model with exponential distribution for wet days.

    Parameters:
        mean_annual: Mean annual precipitation [mm/year]
        wet_day_prob: Probability of a wet day following a dry day [0-1]
        wet_wet_prob: Probability of a wet day following a wet day [0-1]
        alpha: Shape parameter for exponential distribution (default=1.0)
        seed: Random seed for reproducibility (optional)
    """

    def __init__(self,
                 mean_annual: float,
                 wet_day_prob: float = 0.3,
                 wet_wet_prob: float = 0.6,
                 alpha: float = 1.0,
                 seed: Optional[int] = None):
        """Initialize stochastic precipitation generator.

        Args:
            mean_annual: Mean annual precipitation [mm/year]
            wet_day_prob: Probability of wet day after dry day [0-1]
            wet_wet_prob: Probability of wet day after wet day [0-1]
            alpha: Shape parameter for exponential distribution
            seed: Random seed for reproducibility
        """
        self.mean_annual = mean_annual
        self.wet_day_prob = wet_day_prob
        self.wet_wet_prob = wet_wet_prob
        self.alpha = alpha

        # Calculate mean daily precipitation on wet days
        # Assuming ~365 days/year and wet_day_prob as average wet frequency
        avg_wet_days = 365 * wet_day_prob
        self.mean_wet_day = mean_annual / avg_wet_days if avg_wet_days > 0 else 0

        # Initialize random state
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        # Track previous day state (start with dry)
        self.previous_wet = False

        logger.info(f"Initialized PrecipGen: mean_annual={mean_annual} mm/year")

    def generate(self, date: datetime) -> float:
        """Generate precipitation for a single day.

        Args:
            date: Current simulation date

        Returns:
            Daily precipitation [mm/day]
        """
        # Determine if today is wet based on previous day
        if self.previous_wet:
            is_wet = random.random() < self.wet_wet_prob
        else:
            is_wet = random.random() < self.wet_day_prob

        # Generate precipitation amount if wet
        if is_wet:
            # Use exponential distribution for precipitation amount
            precip = np.random.exponential(self.mean_wet_day / self.alpha)
            self.previous_wet = True
        else:
            precip = 0.0
            self.previous_wet = False

        return max(0.0, precip)


class TempGen:
    """Stochastic daily temperature (min/max) generator.

    Generates synthetic daily minimum and maximum temperature time series
    using sinusoidal annual cycle with random perturbations.

    Parameters:
        mean_tmin: Mean annual minimum temperature [°C]
        mean_tmax: Mean annual maximum temperature [°C]
        amplitude_tmin: Seasonal amplitude for Tmin [°C] (default=10)
        amplitude_tmax: Seasonal amplitude for Tmax [°C] (default=10)
        std_tmin: Standard deviation for daily Tmin variation [°C] (default=3)
        std_tmax: Standard deviation for daily Tmax variation [°C] (default=3)
        seed: Random seed for reproducibility (optional)
    """

    def __init__(self,
                 mean_tmin: float,
                 mean_tmax: float,
                 amplitude_tmin: float = 10.0,
                 amplitude_tmax: float = 10.0,
                 std_tmin: float = 3.0,
                 std_tmax: float = 3.0,
                 seed: Optional[int] = None):
        """Initialize stochastic temperature generator.

        Args:
            mean_tmin: Mean annual minimum temperature [°C]
            mean_tmax: Mean annual maximum temperature [°C]
            amplitude_tmin: Seasonal amplitude for Tmin [°C]
            amplitude_tmax: Seasonal amplitude for Tmax [°C]
            std_tmin: Standard deviation for daily Tmin variation [°C]
            std_tmax: Standard deviation for daily Tmax variation [°C]
            seed: Random seed for reproducibility
        """
        self.mean_tmin = mean_tmin
        self.mean_tmax = mean_tmax
        self.amplitude_tmin = amplitude_tmin
        self.amplitude_tmax = amplitude_tmax
        self.std_tmin = std_tmin
        self.std_tmax = std_tmax

        # Initialize random state
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        logger.info(f"Initialized TempGen: mean_tmin={mean_tmin}°C, mean_tmax={mean_tmax}°C")

    def generate(self, date: datetime) -> tuple:
        """Generate minimum and maximum temperature for a single day.

        Args:
            date: Current simulation date

        Returns:
            Tuple of (tmin, tmax) in °C
        """
        # Get day of year (1-366)
        doy = date.timetuple().tm_yday

        # Calculate seasonal component using sinusoidal function
        # Peak in summer (day 200), trough in winter (day 20)
        phase = 2 * math.pi * (doy - 20) / 365

        seasonal_tmin = self.mean_tmin + self.amplitude_tmin * math.sin(phase)
        seasonal_tmax = self.mean_tmax + self.amplitude_tmax * math.sin(phase)

        # Add random daily variation
        tmin = seasonal_tmin + np.random.normal(0, self.std_tmin)
        tmax = seasonal_tmax + np.random.normal(0, self.std_tmax)

        # Ensure tmax >= tmin
        if tmax < tmin:
            tmax = tmin + 1.0

        return tmin, tmax


class StochasticClimate:
    """WGEN stochastic weather generator.

    Orchestrates the three WGEN components (precipitation, temperature, solar radiation)
    to generate synthetic daily weather data using a first-order Markov chain-gamma model
    for precipitation and Fourier series approaches for temperature and solar radiation.

    This class manages state sharing between components and provides a unified interface
    for generating all climate variables for a given date.

    Attributes:
        constants: StationConstants with WGEN parameters
        monthly_params: Dictionary mapping month (1-12) to MonthlyParams
        state: WgenState maintaining shared state between components
        precip_gen: WgenPrecipitation component
        temp_gen: WgenTemperature component
        solar_gen: WgenSolarRadiation component
        deterministic: Whether to use deterministic mode
    """

    def __init__(self, config: Dict[str, Any], yaml_dir: Path):
        """Initialize WGEN stochastic weather generator.

        Args:
            config: Dictionary containing WGEN configuration:
                - param_file: Path to CSV with monthly parameters
                - latitude: Station latitude [degrees]
                - elevation_m: Station elevation [meters]
                - Temperature scalar constants (txmd, txmw, tn, atx, atn, etc.)
                - Solar radiation constants (optional)
                - deterministic: Boolean for reproducible results (optional)
                - seed: Random seed (optional)
            yaml_dir: Directory containing YAML file (for resolving relative paths)

        Raises:
            ConfigurationError: If required parameters are missing
            FileNotFoundError: If parameter CSV file not found
            ValueError: If parameter values are out of range
        """
        self.yaml_dir = yaml_dir
        self.deterministic = config.get('deterministic', False)
        self.seed = config.get('seed', 42 if self.deterministic else None)

        # Log warning if deterministic mode is enabled
        if self.deterministic:
            logger.warning("WGEN in deterministic mode - results are not stochastic")

        # Load monthly parameters from CSV
        param_file = Path(config['param_file'])
        self.monthly_params = load_wgen_parameters(param_file, yaml_dir)

        # Parse station constants from config
        self.constants = parse_wgen_config(config)

        # Initialize shared state (Requirement 6.1, 6.2, 6.3, 6.4)
        self.state = WgenState()

        # Initialize precipitation component
        self.precip_gen = WgenPrecipitation(
            monthly_params=self.monthly_params,
            min_threshold=self.constants.min_rain_mm,
            deterministic=self.deterministic,
            seed=self.seed
        )

        # Initialize temperature component (shares x vector with state)
        self.temp_gen = WgenTemperature(
            constants=self.constants,
            x=self.state.x,
            deterministic=self.deterministic,
            seed=self.seed
        )

        # Initialize solar radiation component (shares x vector with state)
        self.solar_gen = WgenSolarRadiation(
            constants=self.constants,
            x=self.state.x,
            deterministic=self.deterministic,
            seed=self.seed
        )

        logger.info(f"Initialized StochasticClimate (WGEN):")
        logger.info(f"  Latitude: {self.constants.latitude}°")
        logger.info(f"  Elevation: {self.constants.elevation_m}m")
        logger.info(f"  Deterministic: {self.deterministic}")
        if self.deterministic:
            logger.info(f"  Seed: {self.seed}")

    def generate(self, date: datetime) -> Dict[str, float]:
        """Generate weather data for a single day.

        Calls all three WGEN components in sequence, ensuring proper state
        sharing between them (wet/dry status, Fourier coefficients).

        Args:
            date: Current simulation date

        Returns:
            Dictionary with keys:
                - precipitation: Daily precipitation [mm/day]
                - tmin: Minimum temperature [°C]
                - tmax: Maximum temperature [°C]
                - solar_radiation: Solar radiation [MJ/m²/day]
        """
        # Generate precipitation (updates wet/dry state)
        precip = self.precip_gen.generate(date)

        # Update shared state with wet/dry status
        self.state.wet = self.precip_gen.wet
        self.state.rain = precip

        # Generate temperature (uses and updates x vector)
        # Temperature component needs wet/dry state from precipitation
        tmin, tmax = self.temp_gen.generate(date, self.state.wet)

        # Generate solar radiation (uses x[2] from temperature generation)
        # Solar radiation component needs wet/dry state from precipitation
        solar_rad = self.solar_gen.generate(date, self.state.wet)

        return {
            'precipitation': precip,
            'tmin': tmin,
            'tmax': tmax,
            'solar_radiation': solar_rad
        }


class TimeseriesClimate:
    """Load climate data from CSV timeseries files.

    Provides an alternative to stochastic generation by loading actual
    climate data from CSV files.

    Parameters:
        file_path: Path to CSV file containing climate data
        date_column: Name of date column (default='date')
        value_columns: Dictionary mapping variable names to column names
                      e.g., {'precip': 'precip_mm', 'tmin': 'tmin_c'}
    """

    def __init__(self,
                 file_path: Union[str, Path],
                 date_column: str = 'date',
                 value_columns: Optional[Dict[str, str]] = None):
        """Initialize timeseries climate data loader.

        Args:
            file_path: Path to CSV file
            date_column: Name of date column
            value_columns: Dictionary mapping variable names to column names
        """
        self.file_path = Path(file_path)
        self.date_column = date_column
        self.value_columns = value_columns or {}

        # Load data
        self.data = pd.read_csv(self.file_path, parse_dates=[date_column])
        self.data.set_index(date_column, inplace=True)

        logger.info(f"Loaded timeseries climate data from {file_path}")
        logger.info(f"  Date range: {self.data.index.min()} to {self.data.index.max()}")
        logger.info(f"  Variables: {list(self.value_columns.keys())}")

    def get_value(self, date: datetime, variable: str) -> float:
        """Get climate value for a specific date and variable.

        Args:
            date: Date to retrieve data for
            variable: Variable name (must be in value_columns)

        Returns:
            Climate value for the specified date and variable

        Raises:
            KeyError: If variable not found or date not in data
        """
        if variable not in self.value_columns:
            raise KeyError(f"Variable '{variable}' not found in value_columns")

        column_name = self.value_columns[variable]

        try:
            # Convert date to pandas Timestamp for indexing
            date_ts = pd.Timestamp(date)
            value = self.data.loc[date_ts, column_name]
            return float(value)
        except KeyError:
            raise KeyError(f"Date {date} not found in climate data")


def calculate_hargreaves_et(tmin: float,
                            tmax: float,
                            latitude_deg: float,
                            day_of_year: int,
                            coefficient: float = 0.0023) -> float:
    """Calculate reference evapotranspiration using Hargreaves-Samani method.

    This is a wrapper function that calls the Hargreaves ET kernel.

    The Hargreaves-Samani method estimates daily reference evapotranspiration (ET0)
    using only temperature data and latitude. The formula is:

    ET0 = C_H * R_a * (T_mean + 17.8) * sqrt(T_max - T_min)

    Where:
    - C_H is the Hargreaves coefficient (typically 0.0023)
    - R_a is extraterrestrial radiation (MJ/m²/day)
    - T_mean is the mean daily temperature (°C)
    - T_max and T_min are daily max and min temperatures (°C)

    Args:
        tmin: Minimum daily temperature [°C]
        tmax: Maximum daily temperature [°C]
        latitude_deg: Site latitude [degrees]
        day_of_year: Day of year (1-366)
        coefficient: Hargreaves coefficient (default=0.0023)

    Returns:
        Reference evapotranspiration [mm/day]

    Example:
        >>> et0 = calculate_hargreaves_et(
        ...     tmin=10.0, tmax=25.0, latitude_deg=45.5, day_of_year=182
        ... )
        >>> print(f"ET0: {et0:.2f} mm/day")
    """
    # Create kernel parameter and input objects
    params = HargreavesETParams(
        latitude_deg=latitude_deg,
        coefficient=coefficient
    )

    inputs = HargreavesETInputs(
        tmin_c=tmin,
        tmax_c=tmax,
        day_of_year=day_of_year
    )

    # Call the kernel
    outputs = hargreaves_et(inputs, params)

    return outputs.et0_mm


class ClimateManager:
    """Manager for global climate utilities.

    This class coordinates climate data generation/loading and makes it
    available to all components via the global_data dictionary.

    The ClimateManager is initialized from the model's settings block and
    handles stochastic, timeseries, and WGEN modes for precipitation,
    temperature, and solar radiation, with independent mode selection for
    each variable.
    """

    def __init__(self, settings: Dict[str, Any], yaml_dir: Optional[Path] = None):
        """Initialize ClimateManager from model settings.

        Args:
            settings: Climate settings from YAML (settings.climate block)
            yaml_dir: Directory containing YAML file (for resolving relative paths)
        """
        self.settings = settings
        self.yaml_dir = yaml_dir or Path.cwd()

        # Get mode for each climate variable (Requirement 1.1)
        self.precip_mode = settings.get('precipitation', {}).get('mode', 'stochastic')
        self.temp_mode = settings.get('temperature', {}).get('mode', 'stochastic')
        self.solar_mode = settings.get('solar_radiation', {}).get('mode', None)

        # Check if any variable uses WGEN mode
        uses_wgen = 'wgen' in [self.precip_mode, self.temp_mode, self.solar_mode]

        # Initialize WGEN generator if any variable uses it
        self.wgen_gen = None
        if uses_wgen:
            if 'wgen_config' not in settings:
                raise ConfigurationError(
                    "WGEN mode selected but 'wgen_config' not found in climate settings"
                )
            self.wgen_gen = StochasticClimate(settings['wgen_config'], self.yaml_dir)

        # Initialize precipitation generator/loader (Requirement 1.2)
        if self.precip_mode == 'stochastic':
            params = settings['precipitation'].get('params', {})
            self.precip_gen = PrecipGen(**params)
            self.precip_timeseries = None
        elif self.precip_mode == 'timeseries':
            file_path = self.yaml_dir / settings['precipitation']['file']
            column = settings['precipitation'].get('column', 'precip_mm')
            self.precip_timeseries = TimeseriesClimate(
                file_path,
                value_columns={'precip': column}
            )
            self.precip_gen = None
        elif self.precip_mode == 'wgen':
            # WGEN mode - data comes from wgen_gen
            self.precip_gen = None
            self.precip_timeseries = None
        else:
            raise ValueError(f"Invalid precipitation mode: {self.precip_mode}")

        # Initialize temperature generator/loader (Requirement 1.3)
        if self.temp_mode == 'stochastic':
            params = settings['temperature'].get('params', {})
            self.temp_gen = TempGen(**params)
            self.temp_timeseries = None
        elif self.temp_mode == 'timeseries':
            file_path = self.yaml_dir / settings['temperature']['file']
            tmin_col = settings['temperature'].get('tmin_column', 'tmin')
            tmax_col = settings['temperature'].get('tmax_column', 'tmax')
            self.temp_timeseries = TimeseriesClimate(
                file_path,
                value_columns={'tmin': tmin_col, 'tmax': tmax_col}
            )
            self.temp_gen = None
        elif self.temp_mode == 'wgen':
            # WGEN mode - data comes from wgen_gen
            self.temp_gen = None
            self.temp_timeseries = None
        else:
            raise ValueError(f"Invalid temperature mode: {self.temp_mode}")

        # Initialize solar radiation loader if specified (optional)
        self.solar_timeseries = None
        if self.solar_mode == 'timeseries':
            file_path = self.yaml_dir / settings['solar_radiation']['file']
            column = settings['solar_radiation'].get('column', 'solar_rad')
            self.solar_timeseries = TimeseriesClimate(
                file_path,
                value_columns={'solar_rad': column}
            )
        elif self.solar_mode == 'wgen':
            # WGEN mode - data comes from wgen_gen
            pass
        elif self.solar_mode is not None:
            raise ValueError(f"Invalid solar radiation mode: {self.solar_mode}")

        # Store ET calculation settings
        self.et_method = settings.get('et_method', 'hargreaves')
        self.latitude = settings.get('latitude', 0.0)
        self.hargreaves_coef = settings.get('hargreaves_coefficient', 0.0023)

        logger.info(f"Initialized ClimateManager:")
        logger.info(f"  Precipitation mode: {self.precip_mode}")
        logger.info(f"  Temperature mode: {self.temp_mode}")
        logger.info(f"  Solar radiation mode: {self.solar_mode}")
        logger.info(f"  ET method: {self.et_method}")
        logger.info(f"  Uses WGEN: {uses_wgen}")

    def get_climate_data(self, date: datetime) -> Dict[str, float]:
        """Get all climate data for a specific date.

        Supports independent mode selection for each climate variable,
        allowing mixed mode operation (e.g., WGEN precipitation with
        timeseries temperature).

        Args:
            date: Current simulation date

        Returns:
            Dictionary containing:
                - precipitation: Daily precipitation [mm/day]
                - tmin: Minimum temperature [°C]
                - tmax: Maximum temperature [°C]
                - pet: Potential evapotranspiration [mm/day]
                - solar_radiation: Solar radiation [MJ/m²/day] (if available)
        """
        # Generate WGEN data once if needed (Requirement 1.4, 7.5)
        wgen_data = None
        if self.wgen_gen is not None:
            wgen_data = self.wgen_gen.generate(date)

        # Get precipitation (Requirement 1.2, 7.1)
        if self.precip_mode == 'stochastic':
            precip = self.precip_gen.generate(date)
        elif self.precip_mode == 'timeseries':
            precip = self.precip_timeseries.get_value(date, 'precip')
        elif self.precip_mode == 'wgen':
            precip = wgen_data['precipitation']
        else:
            raise ValueError(f"Invalid precipitation mode: {self.precip_mode}")

        # Get temperature (Requirement 1.3, 7.2)
        if self.temp_mode == 'stochastic':
            tmin, tmax = self.temp_gen.generate(date)
        elif self.temp_mode == 'timeseries':
            tmin = self.temp_timeseries.get_value(date, 'tmin')
            tmax = self.temp_timeseries.get_value(date, 'tmax')
        elif self.temp_mode == 'wgen':
            tmin = wgen_data['tmin']
            tmax = wgen_data['tmax']
        else:
            raise ValueError(f"Invalid temperature mode: {self.temp_mode}")

        # Get solar radiation if available (Requirement 7.3)
        solar_rad = None
        if self.solar_mode == 'timeseries':
            solar_rad = self.solar_timeseries.get_value(date, 'solar_rad')
        elif self.solar_mode == 'wgen':
            solar_rad = wgen_data['solar_radiation']

        # Calculate ET (Requirement 7.4)
        if self.et_method == 'hargreaves':
            doy = date.timetuple().tm_yday
            pet = calculate_hargreaves_et(
                tmin, tmax, self.latitude, doy, self.hargreaves_coef
            )
        else:
            # Future: support other ET methods
            pet = 0.0

        # Build result dictionary (Requirement 7.1, 7.2)
        result = {
            'precipitation': precip,
            'tmin': tmin,
            'tmax': tmax,
            'pet': pet,
        }

        # Add solar radiation if available
        if solar_rad is not None:
            result['solar_radiation'] = solar_rad

        return result
