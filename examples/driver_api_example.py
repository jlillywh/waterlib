"""
Example demonstrating the type-safe Driver API.

This example shows how to use the new attribute-based driver access
with IDE autocompletion support instead of magic strings.
"""

from datetime import datetime
from waterlib.core.drivers import DriverRegistry, StochasticDriver

# Create a driver registry
drivers = DriverRegistry()

# Register climate drivers
drivers.register('precipitation', StochasticDriver({'mean': 5.0, 'std': 1.5}, seed=42))
drivers.register('temperature', StochasticDriver({'mean': 15.0, 'std': 5.0}, seed=43))
drivers.register('et', StochasticDriver({'mean': 3.0, 'std': 0.8}, seed=44))

# Access drivers with type-safe API (IDE autocomplete works!)
date = datetime(2020, 6, 15)

# New way: attribute access with autocomplete
precip = drivers.climate.precipitation.get_value(date)
temp = drivers.climate.temperature.get_value(date)
et = drivers.climate.et.get_value(date)

print(f"Date: {date.strftime('%Y-%m-%d')}")
print(f"Precipitation: {precip:.2f} mm")
print(f"Temperature: {temp:.2f} °C")
print(f"ET: {et:.2f} mm")

# Benefits:
# 1. IDE autocompletion: Type "drivers.climate." and see all options
# 2. Typos caught at design time: "drivers.climate.precip" → AttributeError
# 3. Type hints work: hover over .precipitation to see documentation
# 4. No magic strings: "precipitation" vs 'precipitaton' typo caught early
