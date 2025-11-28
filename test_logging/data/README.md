# Data Directory

This directory contains input data files for your waterlib models.

## Files

### wgen_params.csv

Monthly parameters for the WGEN stochastic weather generator. These parameters define the statistical properties of generated climate data including:

- Precipitation occurrence (wet/dry day transitions)
- Precipitation amounts on wet days
- Temperature ranges and variability
- Solar radiation patterns

**Important**: These are example values for a temperate climate (latitude ~40°N). You should calibrate these parameters to your specific location using historical weather data.

See the [WGEN Parameters Guide](../waterlib/templates/WGEN_PARAMETERS_GUIDE.md) for details on parameter estimation.

### climate_timeseries.csv

Example historical climate data showing the required format for timeseries mode. This file contains one year of daily data with:

- `date`: Date in YYYY-MM-DD format
- `precip_mm`: Daily precipitation (mm)
- `tmin_c`: Minimum temperature (°C)
- `tmax_c`: Maximum temperature (°C)
- `et_mm`: Reference evapotranspiration (mm/day) - optional

To use your own climate data:

1. Format your data to match this structure
2. Ensure dates cover your full simulation period
3. Update the model YAML to reference your file:

```yaml
settings:
  climate:
    precipitation:
      mode: timeseries
      file: ../data/your_precip_data.csv
      column: precip_mm
    temperature:
      mode: timeseries
      file: ../data/your_temp_data.csv
      tmin_column: tmin_c
      tmax_column: tmax_c
```

## Adding Your Own Data

You can add additional data files to this directory:

- Reservoir elevation-area-volume curves
- Demand time series
- Observed streamflow for calibration
- Soil parameter datasets
- Land use classifications

Reference these files in your model YAML using relative paths like `../data/your_file.csv`.

## Data Sources

Common sources for climate data:

- **NOAA Climate Data Online**: https://www.ncdc.noaa.gov/cdo-web/
- **PRISM Climate Group**: https://prism.oregonstate.edu/
- **Daymet**: https://daymet.ornl.gov/
- **GridMET**: https://www.climatologylab.org/gridmet.html
- **Local weather stations**: Contact your regional climate center

## Best Practices

1. **Document your data sources** - Add comments or a separate file noting where data came from
2. **Check data quality** - Look for missing values, outliers, and inconsistencies
3. **Use consistent units** - waterlib expects mm for precipitation, °C for temperature
4. **Version control** - Track data files in git if they're small (<10 MB)
5. **Backup large datasets** - Store large files outside the repository
