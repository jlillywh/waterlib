"""
Unit tests for logic components (LaggedValue).
"""

import pytest
from datetime import datetime

from waterlib.components.logic import LaggedValue
from waterlib.core.exceptions import ConfigurationError


class TestLaggedValueConfiguration:
    """Test LaggedValue component configuration validation."""

    def test_valid_configuration(self):
        """Test that valid configuration creates a component successfully."""
        lagged = LaggedValue(
            name="test_lag",
            source="reservoir.elevation",
            initial_value=10.0
        )
        assert lagged.name == "test_lag"
        assert lagged._source_string == "reservoir.elevation"
        assert lagged._initial_value == 10.0

    def test_source_whitespace_stripped(self):
        """Test that whitespace is stripped from source string."""
        lagged = LaggedValue(
            name="test_lag",
            source="  reservoir.elevation  ",
            initial_value=5.0
        )
        assert lagged._source_string == "reservoir.elevation"

    def test_missing_source(self):
        """Test that missing source parameter raises TypeError (Python catches before Pydantic)."""
        with pytest.raises(TypeError, match=r"missing 1 required positional argument: 'source'"):
            LaggedValue(name="test_lag", initial_value=0.0)

    def test_missing_initial_value(self):
        """Test that missing initial_value parameter raises TypeError (Python catches before Pydantic)."""
        with pytest.raises(TypeError, match=r"missing 1 required positional argument: 'initial_value'"):
            LaggedValue(name="test_lag", source="reservoir.elevation")

    def test_empty_source(self):
        """Test that empty source string raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            LaggedValue(
                name="test_lag",
                source="",
                initial_value=0.0
            )

    def test_whitespace_only_source(self):
        """Test that whitespace-only source string raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match=r"configuration error"):
            LaggedValue(
                name="test_lag",
                source="   ",
                initial_value=0.0
            )

    def test_initial_value_types(self):
        """Test that initial_value accepts various types."""
        # Float
        lag_float = LaggedValue(name="lag1", source="comp.out", initial_value=3.14)
        assert lag_float._initial_value == 3.14

        # Integer
        lag_int = LaggedValue(name="lag2", source="comp.out", initial_value=42)
        assert lag_int._initial_value == 42

        # String
        lag_str = LaggedValue(name="lag3", source="comp.out", initial_value="test")
        assert lag_str._initial_value == "test"

        # Boolean
        lag_bool = LaggedValue(name="lag4", source="comp.out", initial_value=True)
        assert lag_bool._initial_value is True

        # Dict
        lag_dict = LaggedValue(name="lag5", source="comp.out", initial_value={"key": "value"})
        assert lag_dict._initial_value == {"key": "value"}

        # List
        lag_list = LaggedValue(name="lag6", source="comp.out", initial_value=[1, 2, 3])
        assert lag_list._initial_value == [1, 2, 3]

        # None
        lag_none = LaggedValue(name="lag7", source="comp.out", initial_value=None)
        assert lag_none._initial_value is None


class TestLaggedValueBehavior:
    """Test LaggedValue component runtime behavior."""

    def test_initial_step_returns_initial_value(self):
        """Test that first step returns initial_value."""
        lagged = LaggedValue(
            name="test_lag",
            source="reservoir.elevation",
            initial_value=10.0
        )

        result = lagged.step(datetime(2023, 1, 1), {})
        assert result == {'value': 10.0}
        assert lagged.outputs == {'value': 10.0}

    def test_second_step_returns_previous_value(self):
        """Test that second step returns value from first step."""
        lagged = LaggedValue(
            name="test_lag",
            source="reservoir.elevation",
            initial_value=10.0
        )

        # First step returns initial value
        lagged.step(datetime(2023, 1, 1), {})

        # Second step should still return initial value (no source connected)
        result = lagged.step(datetime(2023, 1, 2), {})
        assert result == {'value': 10.0}

    def test_immutable_types_not_copied(self):
        """Test that immutable types (int, float, str, bool) are not deep copied."""
        lagged = LaggedValue(
            name="test_lag",
            source="comp.out",
            initial_value=42
        )

        result1 = lagged.step(datetime(2023, 1, 1), {})
        assert result1 == {'value': 42}

        result2 = lagged.step(datetime(2023, 1, 2), {})
        assert result2 == {'value': 42}

    def test_mutable_types_deep_copied(self):
        """Test that mutable types (list, dict, set) are deep copied to prevent reference mutation."""
        initial_dict = {"level": 10.0, "flow": 5.0}
        lagged = LaggedValue(
            name="test_lag",
            source="comp.out",
            initial_value=initial_dict
        )

        result = lagged.step(datetime(2023, 1, 1), {})

        # Modify the result - should not affect the lagged value's internal state
        result['value']['level'] = 999.0

        # Next step should still have original value (not mutated)
        result2 = lagged.step(datetime(2023, 1, 2), {})
        assert result2 == {'value': {"level": 10.0, "flow": 5.0}}

    def test_source_component_not_resolved(self):
        """Test behavior when source component is not yet resolved."""
        lagged = LaggedValue(
            name="test_lag",
            source="reservoir.elevation",
            initial_value=15.0
        )

        # Source not resolved, should use initial_value
        result = lagged.step(datetime(2023, 1, 1), {})
        assert result == {'value': 15.0}

        result2 = lagged.step(datetime(2023, 1, 2), {})
        assert result2 == {'value': 15.0}


class TestLaggedValueTypeCoercion:
    """Test that Pydantic does not coerce initial_value (accepts Any type)."""

    def test_string_not_coerced_to_number(self):
        """Test that string initial_value is not coerced to number."""
        lagged = LaggedValue(
            name="test_lag",
            source="comp.out",
            initial_value="12.5"
        )
        # Should remain a string, not converted to float
        assert lagged._initial_value == "12.5"
        assert isinstance(lagged._initial_value, str)

    def test_number_not_coerced_to_string(self):
        """Test that numeric initial_value is not coerced to string."""
        lagged = LaggedValue(
            name="test_lag",
            source="comp.out",
            initial_value=42
        )
        assert lagged._initial_value == 42
        assert isinstance(lagged._initial_value, int)

    def test_zero_is_valid(self):
        """Test that zero is a valid initial_value."""
        lagged = LaggedValue(
            name="test_lag",
            source="comp.out",
            initial_value=0
        )
        assert lagged._initial_value == 0

        result = lagged.step(datetime(2023, 1, 1), {})
        assert result == {'value': 0}

    def test_negative_value_is_valid(self):
        """Test that negative values are valid initial_value."""
        lagged = LaggedValue(
            name="test_lag",
            source="comp.out",
            initial_value=-10.5
        )
        assert lagged._initial_value == -10.5

        result = lagged.step(datetime(2023, 1, 1), {})
        assert result == {'value': -10.5}


class TestLaggedValueSourceFormat:
    """Test various source string formats."""

    def test_simple_component_reference(self):
        """Test source with just component name (no dot notation)."""
        lagged = LaggedValue(
            name="test_lag",
            source="reservoir",
            initial_value=10.0
        )
        assert lagged._source_string == "reservoir"

    def test_dot_notation_reference(self):
        """Test source with component.output notation."""
        lagged = LaggedValue(
            name="test_lag",
            source="reservoir.elevation",
            initial_value=10.0
        )
        assert lagged._source_string == "reservoir.elevation"

    def test_nested_dot_notation(self):
        """Test source with multiple dots (e.g., module.component.output)."""
        lagged = LaggedValue(
            name="test_lag",
            source="upstream.reservoir.storage",
            initial_value=100.0
        )
        assert lagged._source_string == "upstream.reservoir.storage"

    def test_source_with_underscores(self):
        """Test source with underscores in component/output names."""
        lagged = LaggedValue(
            name="test_lag",
            source="downstream_reservoir.water_level",
            initial_value=5.0
        )
        assert lagged._source_string == "downstream_reservoir.water_level"

    def test_source_with_numbers(self):
        """Test source with numbers in component/output names."""
        lagged = LaggedValue(
            name="test_lag",
            source="pump123.flow_rate",
            initial_value=0.0
        )
        assert lagged._source_string == "pump123.flow_rate"
