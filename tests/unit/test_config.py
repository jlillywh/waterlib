"""
Unit tests for configuration dataclasses.
"""

import pytest
from pathlib import Path
from waterlib.core.config import DriverConfig, ClimateSettings, flatten_driver_config
from waterlib.core.exceptions import ConfigurationError


class TestDriverConfig:
    """Tests for DriverConfig dataclass."""

    def test_driver_config_stochastic_precipitation_params(self):
        """Test that DriverConfig accepts stochastic precipitation parameters."""
        config = DriverConfig(
            mode='stochastic',
            seed=42,
            mean_annual=800.0,
            wet_day_prob=0.3,
            wet_wet_prob=0.6,
            alpha=1.0
        )

        assert config.mode == 'stochastic'
        assert config.seed == 42
        assert config.mean_annual == 800.0
        assert config.wet_day_prob == 0.3
        assert config.wet_wet_prob == 0.6
        assert config.alpha == 1.0

    def test_driver_config_stochastic_temperature_params(self):
        """Test that DriverConfig accepts stochastic temperature parameters."""
        config = DriverConfig(
            mode='stochastic',
            seed=42,
            mean_tmin=5.0,
            mean_tmax=20.0,
            amplitude_tmin=10.0,
            amplitude_tmax=10.0,
            std_tmin=3.0,
            std_tmax=3.0
        )

        assert config.mode == 'stochastic'
        assert config.seed == 42
        assert config.mean_tmin == 5.0
        assert config.mean_tmax == 20.0
        assert config.amplitude_tmin == 10.0
        assert config.amplitude_tmax == 10.0
        assert config.std_tmin == 3.0
        assert config.std_tmax == 3.0

    def test_driver_config_stochastic_et_params(self):
        """Test that DriverConfig accepts stochastic ET parameters."""
        config = DriverConfig(
            mode='stochastic',
            seed=42,
            mean=5.0,
            std=1.0
        )

        assert config.mode == 'stochastic'
        assert config.seed == 42
        assert config.mean == 5.0
        assert config.std == 1.0

    def test_driver_config_timeseries_params(self):
        """Test that DriverConfig accepts timeseries parameters."""
        config = DriverConfig(
            mode='timeseries',
            file='data/precip.csv',
            column='precip_mm'
        )

        assert config.mode == 'timeseries'
        assert config.file == Path('data/precip.csv')
        assert config.column == 'precip_mm'

    def test_driver_config_validates_wet_day_prob_range(self):
        """Test that wet_day_prob must be between 0 and 1."""
        with pytest.raises(ValueError, match="wet_day_prob must be between 0 and 1"):
            DriverConfig(
                mode='stochastic',
                wet_day_prob=1.5
            )

        with pytest.raises(ValueError, match="wet_day_prob must be between 0 and 1"):
            DriverConfig(
                mode='stochastic',
                wet_day_prob=-0.1
            )

    def test_driver_config_validates_wet_wet_prob_range(self):
        """Test that wet_wet_prob must be between 0 and 1."""
        with pytest.raises(ValueError, match="wet_wet_prob must be between 0 and 1"):
            DriverConfig(
                mode='stochastic',
                wet_wet_prob=1.5
            )

        with pytest.raises(ValueError, match="wet_wet_prob must be between 0 and 1"):
            DriverConfig(
                mode='stochastic',
                wet_wet_prob=-0.1
            )

    def test_driver_config_validates_mean_annual_positive(self):
        """Test that mean_annual must be non-negative."""
        with pytest.raises(ValueError, match="mean_annual must be >= 0"):
            DriverConfig(
                mode='stochastic',
                mean_annual=-100.0
            )

    def test_driver_config_validates_alpha_positive(self):
        """Test that alpha must be positive."""
        with pytest.raises(ValueError, match="alpha must be > 0"):
            DriverConfig(
                mode='stochastic',
                alpha=0.0
            )

        with pytest.raises(ValueError, match="alpha must be > 0"):
            DriverConfig(
                mode='stochastic',
                alpha=-1.0
            )

    def test_driver_config_validates_mode(self):
        """Test that invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid climate mode"):
            DriverConfig(mode='invalid_mode')


class TestFlattenDriverConfig:
    """Tests for flatten_driver_config utility function."""

    def test_flatten_nested_params(self):
        """Test flattening nested params dictionary."""
        config = {
            'mode': 'stochastic',
            'seed': 42,
            'params': {
                'mean_annual': 800.0,
                'wet_day_prob': 0.3,
                'wet_wet_prob': 0.6
            }
        }

        result = flatten_driver_config(config)

        assert result['mode'] == 'stochastic'
        assert result['seed'] == 42
        assert result['mean_annual'] == 800.0
        assert result['wet_day_prob'] == 0.3
        assert result['wet_wet_prob'] == 0.6
        assert 'params' not in result

    def test_flatten_flat_format_unchanged(self):
        """Test that flat format (no params) is returned unchanged."""
        config = {
            'mode': 'stochastic',
            'seed': 42,
            'mean_annual': 800.0,
            'wet_day_prob': 0.3
        }

        result = flatten_driver_config(config)

        assert result == config
        assert 'params' not in result

    def test_flatten_empty_params(self):
        """Test flattening with empty params dictionary."""
        config = {
            'mode': 'stochastic',
            'seed': 42,
            'params': {}
        }

        result = flatten_driver_config(config)

        assert result['mode'] == 'stochastic'
        assert result['seed'] == 42
        assert 'params' not in result

    def test_flatten_params_not_dict_raises_error(self):
        """Test that non-dict params raises ConfigurationError."""
        config = {
            'mode': 'stochastic',
            'params': 'not a dict'
        }

        with pytest.raises(ConfigurationError, match="'params' must be a dictionary, got str"):
            flatten_driver_config(config)

    def test_flatten_params_list_raises_error(self):
        """Test that list params raises ConfigurationError."""
        config = {
            'mode': 'stochastic',
            'params': [800, 0.3, 0.6]
        }

        with pytest.raises(ConfigurationError, match="'params' must be a dictionary, got list"):
            flatten_driver_config(config)

    def test_flatten_params_none_raises_error(self):
        """Test that None params raises ConfigurationError."""
        config = {
            'mode': 'stochastic',
            'params': None
        }

        with pytest.raises(ConfigurationError, match="'params' must be a dictionary, got NoneType"):
            flatten_driver_config(config)

    def test_flatten_mixed_format_single_conflict_raises_error(self):
        """Test that mixed format with single conflict raises ConfigurationError."""
        config = {
            'mode': 'stochastic',
            'seed': 42,
            'params': {
                'mean_annual': 800.0,
                'wet_day_prob': 0.3
            },
            'mean_annual': 900.0  # Conflict!
        }

        with pytest.raises(ConfigurationError, match="Parameter\\(s\\) 'mean_annual' specified both in 'params' and at top level"):
            flatten_driver_config(config)

    def test_flatten_mixed_format_multiple_conflicts_raises_error(self):
        """Test that mixed format with multiple conflicts raises ConfigurationError."""
        config = {
            'mode': 'stochastic',
            'seed': 42,
            'params': {
                'mean_annual': 800.0,
                'wet_day_prob': 0.3,
                'wet_wet_prob': 0.6
            },
            'mean_annual': 900.0,  # Conflict!
            'wet_day_prob': 0.4    # Conflict!
        }

        with pytest.raises(ConfigurationError, match="Parameter\\(s\\) .* specified both in 'params' and at top level"):
            flatten_driver_config(config)

    def test_flatten_does_not_modify_original(self):
        """Test that flattening does not modify the original dictionary."""
        config = {
            'mode': 'stochastic',
            'params': {
                'mean_annual': 800.0
            }
        }

        original_config = config.copy()
        result = flatten_driver_config(config)

        # Original should still have params
        assert 'params' in config
        assert config == original_config

        # Result should not have params
        assert 'params' not in result
        assert result['mean_annual'] == 800.0

    def test_flatten_timeseries_mode_no_params(self):
        """Test that timeseries mode without params works correctly."""
        config = {
            'mode': 'timeseries',
            'file': 'data/precip.csv',
            'column': 'precip_mm'
        }

        result = flatten_driver_config(config)

        assert result == config
        assert 'params' not in result

    def test_flatten_preserves_all_top_level_keys(self):
        """Test that all top-level keys are preserved during flattening."""
        config = {
            'mode': 'stochastic',
            'seed': 42,
            'file': 'some_file.csv',
            'params': {
                'mean_annual': 800.0
            }
        }

        result = flatten_driver_config(config)

        assert result['mode'] == 'stochastic'
        assert result['seed'] == 42
        assert result['file'] == 'some_file.csv'
        assert result['mean_annual'] == 800.0
        assert 'params' not in result



class TestClimateSettings:
    """Tests for ClimateSettings.from_dict() with flattening support."""

    def test_precipitation_nested_params_format(self):
        """Test that precipitation with nested params format is parsed correctly."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'seed': 42,
                'params': {
                    'mean_annual': 800.0,
                    'wet_day_prob': 0.3,
                    'wet_wet_prob': 0.6,
                    'alpha': 1.0
                }
            }
        }

        climate = ClimateSettings.from_dict(climate_dict)

        assert climate.precipitation is not None
        assert climate.precipitation.mode == 'stochastic'
        assert climate.precipitation.seed == 42
        assert climate.precipitation.mean_annual == 800.0
        assert climate.precipitation.wet_day_prob == 0.3
        assert climate.precipitation.wet_wet_prob == 0.6
        assert climate.precipitation.alpha == 1.0

    def test_precipitation_flat_format_backward_compatible(self):
        """Test that precipitation with flat format (old style) still works."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'seed': 42,
                'mean_annual': 800.0,
                'wet_day_prob': 0.3,
                'wet_wet_prob': 0.6,
                'alpha': 1.0
            }
        }

        climate = ClimateSettings.from_dict(climate_dict)

        assert climate.precipitation is not None
        assert climate.precipitation.mode == 'stochastic'
        assert climate.precipitation.seed == 42
        assert climate.precipitation.mean_annual == 800.0
        assert climate.precipitation.wet_day_prob == 0.3
        assert climate.precipitation.wet_wet_prob == 0.6
        assert climate.precipitation.alpha == 1.0

    def test_temperature_nested_params_format(self):
        """Test that temperature with nested params format is parsed correctly."""
        climate_dict = {
            'temperature': {
                'mode': 'stochastic',
                'seed': 123,
                'params': {
                    'mean_tmin': 5.0,
                    'mean_tmax': 20.0,
                    'amplitude_tmin': 10.0,
                    'amplitude_tmax': 10.0,
                    'std_tmin': 3.0,
                    'std_tmax': 3.0
                }
            }
        }

        climate = ClimateSettings.from_dict(climate_dict)

        assert climate.temperature is not None
        assert climate.temperature.mode == 'stochastic'
        assert climate.temperature.seed == 123
        assert climate.temperature.mean_tmin == 5.0
        assert climate.temperature.mean_tmax == 20.0
        assert climate.temperature.amplitude_tmin == 10.0
        assert climate.temperature.amplitude_tmax == 10.0
        assert climate.temperature.std_tmin == 3.0
        assert climate.temperature.std_tmax == 3.0

    def test_temperature_flat_format_backward_compatible(self):
        """Test that temperature with flat format (old style) still works."""
        climate_dict = {
            'temperature': {
                'mode': 'stochastic',
                'seed': 123,
                'mean_tmin': 5.0,
                'mean_tmax': 20.0,
                'amplitude_tmin': 10.0,
                'amplitude_tmax': 10.0,
                'std_tmin': 3.0,
                'std_tmax': 3.0
            }
        }

        climate = ClimateSettings.from_dict(climate_dict)

        assert climate.temperature is not None
        assert climate.temperature.mode == 'stochastic'
        assert climate.temperature.seed == 123
        assert climate.temperature.mean_tmin == 5.0
        assert climate.temperature.mean_tmax == 20.0
        assert climate.temperature.amplitude_tmin == 10.0
        assert climate.temperature.amplitude_tmax == 10.0
        assert climate.temperature.std_tmin == 3.0
        assert climate.temperature.std_tmax == 3.0

    def test_et_nested_params_format(self):
        """Test that ET with nested params format is parsed correctly."""
        climate_dict = {
            'et': {
                'mode': 'stochastic',
                'seed': 456,
                'params': {
                    'mean': 5.0,
                    'std': 1.0
                }
            }
        }

        climate = ClimateSettings.from_dict(climate_dict)

        assert climate.et is not None
        assert climate.et.mode == 'stochastic'
        assert climate.et.seed == 456
        assert climate.et.mean == 5.0
        assert climate.et.std == 1.0

    def test_et_flat_format_backward_compatible(self):
        """Test that ET with flat format (old style) still works."""
        climate_dict = {
            'et': {
                'mode': 'stochastic',
                'seed': 456,
                'mean': 5.0,
                'std': 1.0
            }
        }

        climate = ClimateSettings.from_dict(climate_dict)

        assert climate.et is not None
        assert climate.et.mode == 'stochastic'
        assert climate.et.seed == 456
        assert climate.et.mean == 5.0
        assert climate.et.std == 1.0

    def test_all_drivers_nested_params_format(self):
        """Test that all three drivers can use nested params format simultaneously."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'params': {
                    'mean_annual': 800.0,
                    'wet_day_prob': 0.3,
                    'wet_wet_prob': 0.6
                }
            },
            'temperature': {
                'mode': 'stochastic',
                'params': {
                    'mean_tmin': 5.0,
                    'mean_tmax': 20.0
                }
            },
            'et': {
                'mode': 'stochastic',
                'params': {
                    'mean': 5.0,
                    'std': 1.0
                }
            }
        }

        climate = ClimateSettings.from_dict(climate_dict)

        assert climate.precipitation is not None
        assert climate.precipitation.mean_annual == 800.0
        assert climate.temperature is not None
        assert climate.temperature.mean_tmin == 5.0
        assert climate.et is not None
        assert climate.et.mean == 5.0

    def test_mixed_nested_and_flat_formats(self):
        """Test that some drivers can use nested format while others use flat format."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'params': {
                    'mean_annual': 800.0,
                    'wet_day_prob': 0.3,
                    'wet_wet_prob': 0.6
                }
            },
            'temperature': {
                'mode': 'stochastic',
                'mean_tmin': 5.0,
                'mean_tmax': 20.0
            },
            'et': {
                'mode': 'timeseries',
                'file': 'data/et.csv',
                'column': 'et_mm'
            }
        }

        climate = ClimateSettings.from_dict(climate_dict)

        assert climate.precipitation is not None
        assert climate.precipitation.mean_annual == 800.0
        assert climate.temperature is not None
        assert climate.temperature.mean_tmin == 5.0
        assert climate.et is not None
        assert climate.et.mode == 'timeseries'
        assert climate.et.file == Path('data/et.csv')

    def test_timeseries_mode_no_params(self):
        """Test that timeseries mode works without params (as expected)."""
        climate_dict = {
            'precipitation': {
                'mode': 'timeseries',
                'file': 'data/precip.csv',
                'column': 'precip_mm'
            }
        }

        climate = ClimateSettings.from_dict(climate_dict)

        assert climate.precipitation is not None
        assert climate.precipitation.mode == 'timeseries'
        assert climate.precipitation.file == Path('data/precip.csv')
        assert climate.precipitation.column == 'precip_mm'

    def test_invalid_params_type_raises_error(self):
        """Test that invalid params type raises ConfigurationError."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'params': 'not a dict'
            }
        }

        with pytest.raises(ConfigurationError, match="'params' must be a dictionary"):
            ClimateSettings.from_dict(climate_dict)

    def test_mixed_format_in_single_driver_raises_error(self):
        """Test that mixed format in a single driver raises ConfigurationError."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'params': {
                    'mean_annual': 800.0
                },
                'mean_annual': 900.0  # Conflict!
            }
        }

        with pytest.raises(ConfigurationError, match="specified both in 'params' and at top level"):
            ClimateSettings.from_dict(climate_dict)

    def test_empty_climate_dict(self):
        """Test that empty climate dict returns empty ClimateSettings."""
        climate = ClimateSettings.from_dict({})

        assert climate.precipitation is None
        assert climate.temperature is None
        assert climate.et is None
        assert climate.wgen_config is None

    def test_partial_climate_config(self):
        """Test that only some drivers can be configured."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'params': {
                    'mean_annual': 800.0,
                    'wet_day_prob': 0.3,
                    'wet_wet_prob': 0.6
                }
            }
        }

        climate = ClimateSettings.from_dict(climate_dict)

        assert climate.precipitation is not None
        assert climate.temperature is None
        assert climate.et is None


class TestErrorHandling:
    """Tests for comprehensive error handling in climate configuration."""

    def test_missing_mode_parameter(self):
        """Test that missing mode parameter raises ConfigurationError."""
        climate_dict = {
            'precipitation': {
                'params': {
                    'mean_annual': 800.0
                }
            }
        }

        with pytest.raises(ConfigurationError, match=r"\[precipitation\].*Missing required parameter 'mode'"):
            ClimateSettings.from_dict(climate_dict)

    def test_missing_required_stochastic_parameters_precipitation(self):
        """Test that missing required stochastic parameters for precipitation raises error."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'params': {
                    'mean_annual': 800.0
                    # Missing wet_day_prob and wet_wet_prob
                }
            }
        }

        with pytest.raises(ConfigurationError, match=r"\[precipitation\].*missing required parameter"):
            ClimateSettings.from_dict(climate_dict)

    def test_missing_required_stochastic_parameters_temperature(self):
        """Test that missing required stochastic parameters for temperature raises error."""
        climate_dict = {
            'temperature': {
                'mode': 'stochastic',
                'params': {
                    'mean_tmin': 5.0
                    # Missing mean_tmax
                }
            }
        }

        with pytest.raises(ConfigurationError, match=r"\[temperature\].*missing required parameter"):
            ClimateSettings.from_dict(climate_dict)

    def test_missing_required_stochastic_parameters_et(self):
        """Test that missing required stochastic parameters for ET raises error."""
        climate_dict = {
            'et': {
                'mode': 'stochastic',
                'params': {
                    'mean': 5.0
                    # Missing std
                }
            }
        }

        with pytest.raises(ConfigurationError, match=r"\[et\].*missing required parameter"):
            ClimateSettings.from_dict(climate_dict)

    def test_missing_required_timeseries_parameters(self):
        """Test that missing required timeseries parameters raises error."""
        climate_dict = {
            'precipitation': {
                'mode': 'timeseries',
                'file': 'data/precip.csv'
                # Missing column
            }
        }

        with pytest.raises(ConfigurationError, match=r"\[precipitation\].*missing required parameter.*column"):
            ClimateSettings.from_dict(climate_dict)

    def test_unexpected_parameter_stochastic_mode(self):
        """Test that unexpected parameters in stochastic mode raise error."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'params': {
                    'mean_annual': 800.0,
                    'wet_day_prob': 0.3,
                    'wet_wet_prob': 0.6,
                    'invalid_param': 123  # Unexpected!
                }
            }
        }

        with pytest.raises(ConfigurationError, match=r"\[precipitation\].*Unexpected parameter.*invalid_param"):
            ClimateSettings.from_dict(climate_dict)

    def test_unexpected_parameter_timeseries_mode(self):
        """Test that unexpected parameters in timeseries mode raise error."""
        climate_dict = {
            'precipitation': {
                'mode': 'timeseries',
                'file': 'data/precip.csv',
                'column': 'precip_mm',
                'mean_annual': 800.0  # Unexpected for timeseries!
            }
        }

        with pytest.raises(ConfigurationError, match=r"\[precipitation\].*Unexpected parameter.*mean_annual"):
            ClimateSettings.from_dict(climate_dict)

    def test_params_dict_with_timeseries_mode_error(self):
        """Test that using params dict with timeseries mode raises error."""
        climate_dict = {
            'precipitation': {
                'mode': 'timeseries',
                'params': {
                    'file': 'data/precip.csv',
                    'column': 'precip_mm'
                }
            }
        }

        with pytest.raises(ConfigurationError, match=r"\[precipitation\].*'params' dictionary not valid for timeseries mode"):
            ClimateSettings.from_dict(climate_dict)

    def test_invalid_mode_raises_error(self):
        """Test that invalid mode raises ConfigurationError."""
        climate_dict = {
            'precipitation': {
                'mode': 'invalid_mode',
                'params': {
                    'mean_annual': 800.0
                }
            }
        }

        with pytest.raises(ConfigurationError, match=r"\[precipitation\].*Invalid mode 'invalid_mode'"):
            ClimateSettings.from_dict(climate_dict)

    def test_error_message_includes_driver_name_precipitation(self):
        """Test that error messages include driver name for precipitation."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'params': 'not a dict'
            }
        }

        with pytest.raises(ConfigurationError, match=r"\[precipitation\]"):
            ClimateSettings.from_dict(climate_dict)

    def test_error_message_includes_driver_name_temperature(self):
        """Test that error messages include driver name for temperature."""
        climate_dict = {
            'temperature': {
                'mode': 'stochastic',
                'params': {
                    'mean_tmin': 5.0
                    # Missing mean_tmax
                }
            }
        }

        with pytest.raises(ConfigurationError, match=r"\[temperature\]"):
            ClimateSettings.from_dict(climate_dict)

    def test_error_message_includes_driver_name_et(self):
        """Test that error messages include driver name for ET."""
        climate_dict = {
            'et': {
                'mode': 'stochastic',
                'params': {
                    'mean': 5.0,
                    'std': 1.0,
                    'unexpected_param': 999
                }
            }
        }

        with pytest.raises(ConfigurationError, match=r"\[et\]"):
            ClimateSettings.from_dict(climate_dict)

    def test_error_message_lists_valid_parameters(self):
        """Test that error messages list valid parameters when unexpected param found."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'params': {
                    'mean_annual': 800.0,
                    'wet_day_prob': 0.3,
                    'wet_wet_prob': 0.6,
                    'bad_param': 123
                }
            }
        }

        with pytest.raises(ConfigurationError, match=r"Valid parameters:"):
            ClimateSettings.from_dict(climate_dict)

    def test_error_message_lists_required_parameters(self):
        """Test that error messages list required parameters when missing."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'params': {
                    'mean_annual': 800.0
                }
            }
        }

        with pytest.raises(ConfigurationError, match=r"Required parameters:"):
            ClimateSettings.from_dict(climate_dict)

    def test_multiple_missing_parameters_all_listed(self):
        """Test that all missing parameters are listed in error message."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'params': {}
            }
        }

        with pytest.raises(ConfigurationError) as exc_info:
            ClimateSettings.from_dict(climate_dict)

        error_msg = str(exc_info.value)
        assert 'mean_annual' in error_msg
        assert 'wet_day_prob' in error_msg
        assert 'wet_wet_prob' in error_msg

    def test_multiple_unexpected_parameters_all_listed(self):
        """Test that all unexpected parameters are listed in error message."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'params': {
                    'mean_annual': 800.0,
                    'wet_day_prob': 0.3,
                    'wet_wet_prob': 0.6,
                    'bad_param1': 123,
                    'bad_param2': 456
                }
            }
        }

        with pytest.raises(ConfigurationError) as exc_info:
            ClimateSettings.from_dict(climate_dict)

        error_msg = str(exc_info.value)
        assert 'bad_param1' in error_msg
        assert 'bad_param2' in error_msg

    def test_valid_optional_parameters_accepted(self):
        """Test that valid optional parameters are accepted without error."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'seed': 42,  # Optional
                'params': {
                    'mean_annual': 800.0,
                    'wet_day_prob': 0.3,
                    'wet_wet_prob': 0.6,
                    'alpha': 1.5  # Optional
                }
            }
        }

        # Should not raise any error
        climate = ClimateSettings.from_dict(climate_dict)
        assert climate.precipitation.seed == 42
        assert climate.precipitation.alpha == 1.5

    def test_file_parameter_allowed_in_stochastic_mode(self):
        """Test that file parameter is allowed in stochastic mode (for parameter files)."""
        climate_dict = {
            'precipitation': {
                'mode': 'stochastic',
                'file': 'params.csv',  # Allowed for parameter files
                'params': {
                    'mean_annual': 800.0,
                    'wet_day_prob': 0.3,
                    'wet_wet_prob': 0.6
                }
            }
        }

        # Should not raise any error
        climate = ClimateSettings.from_dict(climate_dict)
        assert climate.precipitation.file == Path('params.csv')
