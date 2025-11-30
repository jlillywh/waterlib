from typing import Optional
from pydantic import BaseModel, ConfigDict
from waterlib.core.drivers import DriverRegistry
from datetime import date

class MetStationConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')

    log_precip: bool = True
    log_temp: bool = True  # logs both tmin and tmax
    log_solar: bool = True
    log_et0: bool = True  # Reference ET (ET0)

class MetStation:
    """
    Component to record and persist climate driver data (precipitation, temperature, solar radiation, ET0) for validation and analysis.
    """
    def __init__(self, drivers: DriverRegistry, log_precip: bool = True, log_temp: bool = True,
                 log_solar: bool = True, log_et0: bool = True):
        self.drivers = drivers
        # Create config from parameters
        self.config = MetStationConfig(
            log_precip=log_precip,
            log_temp=log_temp,
            log_solar=log_solar,
            log_et0=log_et0
        )
        self.outputs = []  # List of dicts, one per timestep

    def step(self, sim_date: date):
        row = {}
        # Precipitation
        if self.config.log_precip and self.drivers.climate.has_precipitation():
            row['precip_mm'] = self.drivers.climate.precipitation.get_value(sim_date)
        # Temperature (tmin, tmax)
        if self.config.log_temp and self.drivers.climate.has_temperature():
            temp = self.drivers.climate.temperature.get_value(sim_date)
            # Expect temp to be a dict or object with tmin/tmax
            row['tmin_c'] = temp.get('tmin') if isinstance(temp, dict) else getattr(temp, 'tmin', None)
            row['tmax_c'] = temp.get('tmax') if isinstance(temp, dict) else getattr(temp, 'tmax', None)
        # Solar Radiation
        if self.config.log_solar and self.drivers.climate.has_solar_radiation():
            row['solar_mjm2'] = self.drivers.climate.solar_radiation.get_value(sim_date)
        # Reference ET (ET0)
        if self.config.log_et0 and self.drivers.climate.has_et():
            row['et0_mm'] = self.drivers.climate.et.get_value(sim_date)
        # Persist row
        self.outputs.append(row)

    def to_dataframe(self):
        import pandas as pd
        return pd.DataFrame(self.outputs)

    def export_csv(self, path: str):
        df = self.to_dataframe()
        df.to_csv(path, index=False)
