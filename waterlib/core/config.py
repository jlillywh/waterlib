"""
Configuration dataclasses for waterlib.

This module defines dataclasses for model settings and climate configuration,
providing a structured way to manage simulation parameters.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal, Dict, Any
from pathlib import Path
from waterlib.core.exceptions import ConfigurationError


def flatten_driver_config(driver_dict: Dict[str, Any], driver_name: str = None) -> Dict[str, Any]:
    """Flatten nested params dictionary in driver configuration.

    This utility function handles the documented nested `params:` syntax for
    climate driver configuration, converting it to the flat structure expected
    by DriverConfig. It also validates for mixed format errors where parameters
    appear both inside and outside the params dictionary.

    Args:
        driver_dict: Driver configuration dictionary (may contain 'params')
        driver_name: Name of the driver (e.g., 'precipitation', 'temperature', 'et') for error messages

    Returns:
        Flattened dictionary with params merged to top level

    Raises:
        ConfigurationError: If params is not a dictionary, or if mixed format
            is detected (same parameter in both params and top level)

    Examples:
        >>> # Nested format (documented syntax)
        >>> config = {'mode': 'stochastic', 'params': {'mean_annual': 800}}
        >>> flatten_driver_config(config)
        {'mode': 'stochastic', 'mean_annual': 800}

        >>> # Flat format (backward compatible)
        >>> config = {'mode': 'stochastic', 'mean_annual': 800}
        >>> flatten_driver_config(config)
        {'mode': 'stochastic', 'mean_annual': 800}

        >>> # Mixed format (error)
        >>> config = {'mode': 'stochastic', 'params': {'mean_annual': 800}, 'mean_annual': 900}
        >>> flatten_driver_config(config)
        ConfigurationError: Parameter 'mean_annual' specified both in 'params' and at top level
    """
    # Make a copy to avoid modifying the original
    flattened = driver_dict.copy()

    # Build error prefix for better error messages
    error_prefix = f"[{driver_name}] " if driver_name else ""

    # If no params key, return as-is (flat format or no parameters)
    if 'params' not in flattened:
        return flattened

    # Extract params
    params = flattened.pop('params')

    # Validate that params is a dictionary
    if not isinstance(params, dict):
        raise ConfigurationError(
            f"{error_prefix}'params' must be a dictionary, got {type(params).__name__}"
        )

    # Check for mixed format (parameters in both params and top level)
    conflicts = set(params.keys()) & set(flattened.keys())
    if conflicts:
        conflict_list = ', '.join(f"'{k}'" for k in sorted(conflicts))
        raise ConfigurationError(
            f"{error_prefix}Parameter(s) {conflict_list} specified both in 'params' and at top level. "
            f"Use either nested 'params:' format or flat format, not both."
        )

    # Merge params into top level
    flattened.update(params)

    return flattened


def validate_driver_config_pre_flatten(driver_dict: Dict[str, Any], driver_name: str) -> None:
    """Validate driver configuration before flattening.

    This function checks for mode-specific issues that need to be caught before
    the params dictionary is flattened, such as using params dict with timeseries mode.

    Args:
        driver_dict: Original driver configuration dictionary (before flattening)
        driver_name: Name of the driver (e.g., 'precipitation', 'temperature', 'et')

    Raises:
        ConfigurationError: If validation fails with detailed error message
    """
    mode = driver_dict.get('mode')

    # Check if params dict was used with timeseries mode (not appropriate)
    if mode == 'timeseries' and 'params' in driver_dict:
        raise ConfigurationError(
            f"[{driver_name}] 'params' dictionary not valid for timeseries mode. "
            f"Timeseries mode uses flat parameters: file, column"
        )


def validate_driver_config(driver_dict: Dict[str, Any], driver_name: str) -> None:
    """Validate driver configuration for mode-specific requirements.

    This function validates that:
    - Required parameters are present for the specified mode
    - No unexpected parameters are present for the specified mode
    - Mode-specific parameter constraints are met

    Args:
        driver_dict: Flattened driver configuration dictionary
        driver_name: Name of the driver (e.g., 'precipitation', 'temperature', 'et')

    Raises:
        ConfigurationError: If validation fails with detailed error message
    """
    mode = driver_dict.get('mode')

    if not mode:
        raise ConfigurationError(
            f"[{driver_name}] Missing required parameter 'mode'. "
            f"Valid modes: 'stochastic', 'timeseries', 'wgen'"
        )

    # Define valid parameters for each mode
    common_params = {'mode', 'seed'}
    timeseries_params = common_params | {'file', 'column'}
    wgen_params = common_params  # WGEN uses wgen_config, not driver-level params

    # Define stochastic parameters by driver type
    stochastic_precip_params = common_params | {
        'mean_annual', 'wet_day_prob', 'wet_wet_prob', 'alpha', 'file'
    }
    stochastic_temp_params = common_params | {
        'mean_tmin', 'mean_tmax', 'amplitude_tmin', 'amplitude_tmax',
        'std_tmin', 'std_tmax', 'file'
    }
    stochastic_et_params = common_params | {
        'mean', 'std', 'file'
    }

    # Determine valid parameters based on mode and driver type
    if mode == 'timeseries':
        valid_params = timeseries_params
        required_params = {'file', 'column'}

    elif mode == 'wgen':
        valid_params = wgen_params
        required_params = set()

    elif mode == 'stochastic':
        # Determine which stochastic parameters are valid based on driver type
        if driver_name == 'precipitation':
            valid_params = stochastic_precip_params
            required_params = {'mean_annual', 'wet_day_prob', 'wet_wet_prob'}
        elif driver_name == 'temperature':
            valid_params = stochastic_temp_params
            required_params = {'mean_tmin', 'mean_tmax'}
        elif driver_name == 'et':
            valid_params = stochastic_et_params
            required_params = {'mean', 'std'}
        else:
            # Unknown driver type, allow all stochastic params
            valid_params = stochastic_precip_params | stochastic_temp_params | stochastic_et_params
            required_params = set()

    else:
        raise ConfigurationError(
            f"[{driver_name}] Invalid mode '{mode}'. "
            f"Valid modes: 'stochastic', 'timeseries', 'wgen'"
        )

    # Check for missing required parameters
    provided_params = set(driver_dict.keys())
    missing_params = required_params - provided_params

    if missing_params:
        missing_list = ', '.join(f"'{p}'" for p in sorted(missing_params))
        required_list = ', '.join(f"'{p}'" for p in sorted(required_params))
        raise ConfigurationError(
            f"[{driver_name}] {mode.capitalize()} mode missing required parameter(s): {missing_list}. "
            f"Required parameters: {required_list}"
        )

    # Check for unexpected parameters
    unexpected_params = provided_params - valid_params

    if unexpected_params:
        unexpected_list = ', '.join(f"'{p}'" for p in sorted(unexpected_params))
        valid_list = ', '.join(f"'{p}'" for p in sorted(valid_params))
        raise ConfigurationError(
            f"[{driver_name}] Unexpected parameter(s) for {mode} mode: {unexpected_list}. "
            f"Valid parameters: {valid_list}"
        )


@dataclass
class DriverConfig:
    """Configuration for a single climate driver.

    Attributes:
        mode: Driver mode - 'stochastic', 'timeseries', or 'wgen' for WGEN synthetic data
        seed: Random seed for stochastic mode (optional)
        file: Path to CSV file containing parameters (stochastic) or data (timeseries)
        column: Column name in CSV for timeseries mode (optional)

        Stochastic mode parameters (precipitation):
        mean_annual: Mean annual precipitation [mm/year]
        wet_day_prob: Probability of wet day after dry day [0-1]
        wet_wet_prob: Probability of wet day after wet day [0-1]
        alpha: Shape parameter for exponential distribution (default=1.0)

        Stochastic mode parameters (temperature):
        mean_tmin: Mean annual minimum temperature [°C]
        mean_tmax: Mean annual maximum temperature [°C]
        amplitude_tmin: Seasonal amplitude for Tmin [°C] (default=10)
        amplitude_tmax: Seasonal amplitude for Tmax [°C] (default=10)
        std_tmin: Standard deviation for daily Tmin variation [°C] (default=3)
        std_tmax: Standard deviation for daily Tmax variation [°C] (default=3)

        Stochastic mode parameters (ET):
        mean: Mean evapotranspiration value
        std: Standard deviation for evapotranspiration
    """
    mode: Literal['stochastic', 'timeseries', 'wgen']
    seed: Optional[int] = None
    file: Optional[Path] = None
    column: Optional[str] = None

    # Stochastic mode parameters (precipitation)
    mean_annual: Optional[float] = None
    wet_day_prob: Optional[float] = None
    wet_wet_prob: Optional[float] = None
    alpha: Optional[float] = None

    # Stochastic mode parameters (temperature)
    mean_tmin: Optional[float] = None
    mean_tmax: Optional[float] = None
    amplitude_tmin: Optional[float] = None
    amplitude_tmax: Optional[float] = None
    std_tmin: Optional[float] = None
    std_tmax: Optional[float] = None

    # Stochastic mode parameters (ET)
    mean: Optional[float] = None
    std: Optional[float] = None

    def __post_init__(self):
        """Convert file string to Path if needed and validate configuration."""
        if self.file is not None and isinstance(self.file, str):
            self.file = Path(self.file)

        # Validate mode
        valid_modes = ['stochastic', 'timeseries', 'wgen']
        if self.mode not in valid_modes:
            raise ValueError(
                f"Invalid climate mode '{self.mode}'. Must be one of: {valid_modes}"
            )

        # Validate stochastic parameters if provided
        if self.wet_day_prob is not None and not 0 <= self.wet_day_prob <= 1:
            raise ValueError(
                f"wet_day_prob must be between 0 and 1, got {self.wet_day_prob}"
            )

        if self.wet_wet_prob is not None and not 0 <= self.wet_wet_prob <= 1:
            raise ValueError(
                f"wet_wet_prob must be between 0 and 1, got {self.wet_wet_prob}"
            )

        if self.mean_annual is not None and self.mean_annual < 0:
            raise ValueError(
                f"mean_annual must be >= 0, got {self.mean_annual}"
            )

        if self.alpha is not None and self.alpha <= 0:
            raise ValueError(
                f"alpha must be > 0, got {self.alpha}"
            )


@dataclass
class WgenConfig:
    """WGEN weather generator configuration.

    Attributes:
        param_file: Path to CSV file with monthly parameters
        latitude: Station latitude [degrees, -90 to 90]
        elevation_m: Station elevation [meters, >= 0]
        txmd: Mean Tmax dry [°C]
        txmw: Mean Tmax wet [°C]
        tn: Mean Tmin [°C]
        atx: Amplitude Tmax [°C]
        atn: Amplitude Tmin [°C]
        cvtx: CV Tmax mean [>= 0]
        acvtx: CV Tmax amplitude
        cvtn: CV Tmin mean [>= 0]
        acvtn: CV Tmin amplitude
        dt_day: Peak temperature day of year [1-366]
        rs_mean: Mean solar radiation [MJ/m²/day]
        rs_amplitude: Solar radiation amplitude [MJ/m²/day]
        rs_cv: Solar radiation coefficient of variation [>= 0]
        rs_wet_factor: Solar radiation reduction factor for wet days [0-1]
        min_rain_mm: Minimum precipitation threshold [mm, >= 0]
        deterministic: If True, use fixed random seed
        seed: Random seed for deterministic mode
    """
    param_file: Path
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
    deterministic: bool = False
    seed: Optional[int] = None

    def __post_init__(self):
        """Validate WGEN configuration parameters."""
        # Convert param_file to Path if needed
        if isinstance(self.param_file, str):
            self.param_file = Path(self.param_file)

        # Validate latitude
        if not -90 <= self.latitude <= 90:
            raise ValueError(
                f"WGEN parameter 'latitude' must be between -90 and 90, got {self.latitude}"
            )

        # Validate elevation
        if self.elevation_m < 0:
            raise ValueError(
                f"WGEN parameter 'elevation_m' must be >= 0, got {self.elevation_m}"
            )

        # Validate coefficients of variation (must be non-negative)
        if self.cvtx < 0:
            raise ValueError(
                f"WGEN parameter 'cvtx' must be >= 0, got {self.cvtx}"
            )
        if self.cvtn < 0:
            raise ValueError(
                f"WGEN parameter 'cvtn' must be >= 0, got {self.cvtn}"
            )
        if self.rs_cv < 0:
            raise ValueError(
                f"WGEN parameter 'rs_cv' must be >= 0, got {self.rs_cv}"
            )

        # Validate dt_day
        if not 1 <= self.dt_day <= 366:
            raise ValueError(
                f"WGEN parameter 'dt_day' must be between 1 and 366, got {self.dt_day}"
            )

        # Validate min_rain_mm
        if self.min_rain_mm < 0:
            raise ValueError(
                f"WGEN parameter 'min_rain_mm' must be >= 0, got {self.min_rain_mm}"
            )

        # Validate rs_wet_factor
        if not 0 <= self.rs_wet_factor <= 1:
            raise ValueError(
                f"WGEN parameter 'rs_wet_factor' must be between 0 and 1, got {self.rs_wet_factor}"
            )

    @classmethod
    def from_dict(cls, wgen_dict: Dict[str, Any]) -> 'WgenConfig':
        """Create WgenConfig from dictionary.

        Args:
            wgen_dict: Dictionary containing WGEN configuration

        Returns:
            WgenConfig instance

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Required parameters
        required_params = [
            'param_file', 'latitude', 'elevation_m', 'txmd', 'txmw', 'tn',
            'atx', 'atn', 'cvtx', 'acvtx', 'cvtn', 'acvtn', 'dt_day'
        ]

        missing_params = [p for p in required_params if p not in wgen_dict]
        if missing_params:
            raise ValueError(
                f"WGEN configuration missing required parameters: {missing_params}"
            )

        # Extract all parameters with defaults for optional ones
        return cls(
            param_file=wgen_dict['param_file'],
            latitude=float(wgen_dict['latitude']),
            elevation_m=float(wgen_dict['elevation_m']),
            txmd=float(wgen_dict['txmd']),
            txmw=float(wgen_dict['txmw']),
            tn=float(wgen_dict['tn']),
            atx=float(wgen_dict['atx']),
            atn=float(wgen_dict['atn']),
            cvtx=float(wgen_dict['cvtx']),
            acvtx=float(wgen_dict['acvtx']),
            cvtn=float(wgen_dict['cvtn']),
            acvtn=float(wgen_dict['acvtn']),
            dt_day=int(wgen_dict['dt_day']),
            rs_mean=float(wgen_dict.get('rs_mean', 15.0)),
            rs_amplitude=float(wgen_dict.get('rs_amplitude', 10.0)),
            rs_cv=float(wgen_dict.get('rs_cv', 0.3)),
            rs_wet_factor=float(wgen_dict.get('rs_wet_factor', 0.7)),
            min_rain_mm=float(wgen_dict.get('min_rain_mm', 0.254)),
            deterministic=bool(wgen_dict.get('deterministic', False)),
            seed=wgen_dict.get('seed')
        )


@dataclass
class ClimateSettings:
    """Climate driver configuration.

    Attributes:
        precipitation: Configuration for precipitation driver
        temperature: Configuration for temperature driver
        et: Configuration for evapotranspiration driver
        wgen_config: WGEN configuration (required if any driver uses 'wgen' mode)
    """
    precipitation: Optional[DriverConfig] = None
    temperature: Optional[DriverConfig] = None
    et: Optional[DriverConfig] = None
    wgen_config: Optional[WgenConfig] = None

    @classmethod
    def from_dict(cls, climate_dict: Dict[str, Any]) -> 'ClimateSettings':
        """Create ClimateSettings from dictionary.

        Args:
            climate_dict: Dictionary containing climate configuration

        Returns:
            ClimateSettings instance

        Raises:
            ValueError: If WGEN mode is used but wgen_config is missing
            ConfigurationError: If params structure is invalid, required parameters
                are missing, or unexpected parameters are present
        """
        if not climate_dict:
            return cls()

        # Parse each driver config with flattening and validation
        precipitation = None
        if 'precipitation' in climate_dict:
            try:
                precip_dict = climate_dict['precipitation']
                # Validate before flattening (checks for params dict with timeseries mode)
                validate_driver_config_pre_flatten(precip_dict, driver_name='precipitation')
                # Flatten nested params if present
                flattened_precip = flatten_driver_config(precip_dict, driver_name='precipitation')
                # Validate configuration
                validate_driver_config(flattened_precip, driver_name='precipitation')
                precipitation = DriverConfig(**flattened_precip)
            except (ConfigurationError, ValueError) as e:
                # Re-raise with context if not already included
                if '[precipitation]' not in str(e):
                    raise ConfigurationError(f"[precipitation] {str(e)}") from e
                raise

        temperature = None
        if 'temperature' in climate_dict:
            try:
                temp_dict = climate_dict['temperature']
                # Validate before flattening (checks for params dict with timeseries mode)
                validate_driver_config_pre_flatten(temp_dict, driver_name='temperature')
                # Flatten nested params if present
                flattened_temp = flatten_driver_config(temp_dict, driver_name='temperature')
                # Validate configuration
                validate_driver_config(flattened_temp, driver_name='temperature')
                temperature = DriverConfig(**flattened_temp)
            except (ConfigurationError, ValueError) as e:
                # Re-raise with context if not already included
                if '[temperature]' not in str(e):
                    raise ConfigurationError(f"[temperature] {str(e)}") from e
                raise

        et = None
        if 'et' in climate_dict:
            try:
                et_dict = climate_dict['et']
                # Validate before flattening (checks for params dict with timeseries mode)
                validate_driver_config_pre_flatten(et_dict, driver_name='et')
                # Flatten nested params if present
                flattened_et = flatten_driver_config(et_dict, driver_name='et')
                # Validate configuration
                validate_driver_config(flattened_et, driver_name='et')
                et = DriverConfig(**flattened_et)
            except (ConfigurationError, ValueError) as e:
                # Re-raise with context if not already included
                if '[et]' not in str(e):
                    raise ConfigurationError(f"[et] {str(e)}") from e
                raise

        # Parse WGEN config if present
        wgen_config = None
        if 'wgen_config' in climate_dict:
            wgen_config = WgenConfig.from_dict(climate_dict['wgen_config'])

        # Validate that wgen_config is provided if any driver uses 'wgen' mode
        uses_wgen = any(
            driver and driver.mode == 'wgen'
            for driver in [precipitation, temperature, et]
        )

        if uses_wgen and wgen_config is None:
            raise ValueError(
                "WGEN mode is used for one or more climate variables, "
                "but 'wgen_config' is not provided in climate settings"
            )

        return cls(
            precipitation=precipitation,
            temperature=temperature,
            et=et,
            wgen_config=wgen_config
        )


@dataclass
class ModelSettings:
    """Model configuration settings.

    Attributes:
        start_date: Simulation start date
        end_date: Simulation end date
        timestep: Timestep frequency (pandas frequency string, e.g., '1D' for daily)
        climate: Climate driver configuration (optional)
    """
    start_date: datetime
    end_date: datetime
    timestep: str = '1D'
    climate: Optional[ClimateSettings] = None

    @classmethod
    def from_dict(cls, settings_dict: Dict[str, Any]) -> 'ModelSettings':
        """Create ModelSettings from dictionary.

        Args:
            settings_dict: Dictionary containing settings from YAML

        Returns:
            ModelSettings instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Extract required fields
        if 'start_date' not in settings_dict:
            raise ValueError("Missing required setting: 'start_date'")
        if 'end_date' not in settings_dict:
            raise ValueError("Missing required setting: 'end_date'")

        # Parse dates
        start_date_str = settings_dict['start_date']
        end_date_str = settings_dict['end_date']

        # Convert to datetime if strings
        if isinstance(start_date_str, str):
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError as e:
                raise ValueError(
                    f"Invalid start_date format: '{start_date_str}'. "
                    f"Expected YYYY-MM-DD format. Error: {str(e)}"
                )
        else:
            start_date = start_date_str

        if isinstance(end_date_str, str):
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError as e:
                raise ValueError(
                    f"Invalid end_date format: '{end_date_str}'. "
                    f"Expected YYYY-MM-DD format. Error: {str(e)}"
                )
        else:
            end_date = end_date_str

        # Validate date range
        if end_date < start_date:
            raise ValueError(
                f"end_date ({end_date.strftime('%Y-%m-%d')}) must be >= "
                f"start_date ({start_date.strftime('%Y-%m-%d')})"
            )

        # Extract optional fields
        timestep = settings_dict.get('timestep', '1D')

        # Parse climate settings if present
        climate = None
        if 'climate' in settings_dict:
            climate = ClimateSettings.from_dict(settings_dict['climate'])

        return cls(
            start_date=start_date,
            end_date=end_date,
            timestep=timestep,
            climate=climate
        )
