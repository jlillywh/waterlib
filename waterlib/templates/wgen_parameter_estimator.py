"""
WGEN Parameter Estimation Utility

This module provides functions to estimate WGEN parameters from historical
climate data. Use this to generate parameter files for your location.

The estimator produces:
- Monthly precipitation parameters (PWW, PWD, ALPHA, BETA) in CSV format
- Constant temperature/radiation parameters in YAML format

Usage:
    python -m waterlib.templates.wgen_parameter_estimator \
        --climate data/climate.csv \
        --latitude 40.76 \
        --output-csv data/wgen_params.csv \
        --output-yaml data/wgen_constants.yaml

Required CSV columns:
    - date: Date in YYYY-MM-DD format
    - precip_mm: Daily precipitation (mm)
    - tmax_c: Daily maximum temperature (°C)
    - tmin_c: Daily minimum temperature (°C)
    - solar_mjm2: Daily solar radiation (MJ/m²/day)
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Tuple
import argparse
from pathlib import Path


def estimate_precipitation_params(precip_series: pd.Series,
                                   dates: pd.Series,
                                   wet_threshold: float = 0.254) -> Dict[str, list]:
    """
    Estimate monthly precipitation parameters from historical data.

    Args:
        precip_series: Daily precipitation values (mm)
        dates: Corresponding dates
        wet_threshold: Minimum precipitation to consider a day "wet" (mm)

    Returns:
        Dictionary with keys 'pww', 'pwd', 'alpha', 'beta', each containing 12 monthly values
    """
    df = pd.DataFrame({
        'date': pd.to_datetime(dates),
        'precip': precip_series
    })
    df['month'] = df['date'].dt.month
    df['wet'] = df['precip'] > wet_threshold
    df['prev_wet'] = df['wet'].shift(1)

    pww_list = []
    pwd_list = []
    alpha_list = []
    beta_list = []

    for month in range(1, 13):
        month_data = df[df['month'] == month].copy()

        # Remove rows with NaN in prev_wet (first row of dataset)
        month_data = month_data.dropna(subset=['prev_wet'])

        if len(month_data) < 10:
            print(f"Warning: Only {len(month_data)} days for month {month}")
            # Use defaults for insufficient data
            pww_list.append(0.5)
            pwd_list.append(0.3)
            alpha_list.append(0.7)
            beta_list.append(10.0)
            continue

        # Calculate transition probabilities
        wet_following_wet = month_data[month_data['prev_wet'] == True]['wet'].sum()
        total_wet_days = (month_data['prev_wet'] == True).sum()

        wet_following_dry = month_data[month_data['prev_wet'] == False]['wet'].sum()
        total_dry_days = (month_data['prev_wet'] == False).sum()

        p_wet_wet = wet_following_wet / total_wet_days if total_wet_days > 0 else 0.5
        p_wet_dry = wet_following_dry / total_dry_days if total_dry_days > 0 else 0.3

        # Fit gamma distribution to wet day amounts
        wet_amounts = month_data[month_data['wet']]['precip'].values

        if len(wet_amounts) >= 3:
            # Method of moments for gamma distribution
            mean_precip = np.mean(wet_amounts)
            var_precip = np.var(wet_amounts)

            # alpha = mean^2 / variance, beta = variance / mean
            if var_precip > 0:
                alpha = (mean_precip ** 2) / var_precip
                beta = var_precip / mean_precip
            else:
                alpha = 1.0
                beta = mean_precip
        else:
            # Not enough data, use defaults
            alpha = 0.7
            beta = 10.0

        pww_list.append(round(p_wet_wet, 4))
        pwd_list.append(round(p_wet_dry, 4))
        alpha_list.append(round(alpha, 4))
        beta_list.append(round(beta, 3))

    return {
        'pww': pww_list,
        'pwd': pwd_list,
        'alpha': alpha_list,
        'beta': beta_list
    }


def estimate_temperature_params(tmax_series: pd.Series,
                                tmin_series: pd.Series,
                                precip_series: pd.Series,
                                dates: pd.Series,
                                wet_threshold: float = 0.254) -> Dict[str, float]:
    """
    Estimate constant temperature parameters from historical data.

    Args:
        tmax_series: Daily maximum temperature values (°C)
        tmin_series: Daily minimum temperature values (°C)
        precip_series: Daily precipitation values (mm)
        dates: Corresponding dates
        wet_threshold: Minimum precipitation to consider a day "wet" (mm)

    Returns:
        Dictionary of constant temperature parameters (TXMD, ATX, TXMW, TN, ATN, CVTX, ACVTX, CVTN, ACVTN)
    """
    df = pd.DataFrame({
        'date': pd.to_datetime(dates),
        'tmax': tmax_series,
        'tmin': tmin_series,
        'precip': precip_series
    })
    df['wet'] = df['precip'] > wet_threshold
    df['doy'] = df['date'].dt.dayofyear

    # Separate wet and dry days
    dry_tmax = df[~df['wet']]['tmax']
    wet_tmax = df[df['wet']]['tmax']

    # Calculate mean temperatures
    txmd = dry_tmax.mean() if len(dry_tmax) > 0 else df['tmax'].mean()
    txmw = wet_tmax.mean() if len(wet_tmax) > 0 else df['tmax'].mean()
    tn = df['tmin'].mean()

    # Estimate amplitude by fitting sinusoid to tmax
    from scipy.optimize import curve_fit

    def sinusoid(doy, mean, amplitude, peak_day):
        return mean + amplitude * np.cos(2 * np.pi * (doy - peak_day) / 365)

    try:
        popt, _ = curve_fit(sinusoid, df['doy'], df['tmax'],
                           p0=[df['tmax'].mean(), 10, 200],
                           maxfev=5000)
        _, atx, _ = popt
        atx = abs(atx)
    except:
        # Fallback: use simple max-min
        monthly_means = df.groupby(df['date'].dt.month)['tmax'].mean()
        atx = (monthly_means.max() - monthly_means.min()) / 2

    # Estimate amplitude for tmin
    try:
        popt, _ = curve_fit(sinusoid, df['doy'], df['tmin'],
                           p0=[df['tmin'].mean(), 8, 200],
                           maxfev=5000)
        _, atn, _ = popt
        atn = abs(atn)
    except:
        # Fallback: use simple max-min
        monthly_means = df.groupby(df['date'].dt.month)['tmin'].mean()
        atn = (monthly_means.max() - monthly_means.min()) / 2

    # Calculate coefficient of variation for tmax
    # Use absolute temperature in Kelvin for CV calculation to avoid issues with negative Celsius
    tmax_k = df['tmax'] + 273.15
    cvtx = tmax_k.std() / tmax_k.mean() if tmax_k.mean() != 0 else 0.02

    # Calculate coefficient of variation for tmin
    tmin_k = df['tmin'] + 273.15
    cvtn = tmin_k.std() / tmin_k.mean() if tmin_k.mean() != 0 else 0.02

    # Amplitude CV (typically negative, indicating less variation in amplitude)
    acvtx = -cvtx * 0.5  # Typical ratio
    acvtn = -cvtn * 0.5  # Typical ratio

    return {
        'txmd': round(txmd, 2),
        'atx': round(atx, 2),
        'txmw': round(txmw, 2),
        'tn': round(tn, 2),
        'atn': round(atn, 2),
        'cvtx': round(cvtx, 4),
        'acvtx': round(acvtx, 4),
        'cvtn': round(cvtn, 4),
        'acvtn': round(acvtn, 4)
    }


def estimate_radiation_params(solar_series: pd.Series,
                              precip_series: pd.Series,
                              dates: pd.Series,
                              wet_threshold: float = 0.254) -> Dict[str, float]:
    """
    Estimate constant radiation parameters from historical data.

    Args:
        solar_series: Daily solar radiation values (MJ/m²/day)
        precip_series: Daily precipitation values (mm)
        dates: Corresponding dates
        wet_threshold: Minimum precipitation to consider a day "wet" (mm)

    Returns:
        Dictionary of constant radiation parameters (RMD, AR, RMW)
    """
    df = pd.DataFrame({
        'date': pd.to_datetime(dates),
        'solar': solar_series,
        'precip': precip_series
    })
    df['wet'] = df['precip'] > wet_threshold
    df['doy'] = df['date'].dt.dayofyear

    # Separate wet and dry days
    dry_solar = df[~df['wet']]['solar']
    wet_solar = df[df['wet']]['solar']

    # Calculate mean radiation
    rmd = dry_solar.mean() if len(dry_solar) > 0 else df['solar'].mean()
    rmw = wet_solar.mean() if len(wet_solar) > 0 else df['solar'].mean()

    # Estimate amplitude by fitting sinusoid
    from scipy.optimize import curve_fit

    def sinusoid(doy, mean, amplitude, peak_day):
        return mean + amplitude * np.cos(2 * np.pi * (doy - peak_day) / 365)

    try:
        popt, _ = curve_fit(sinusoid, df['doy'], df['solar'],
                           p0=[df['solar'].mean(), 5, 172],
                           maxfev=5000)
        _, ar, _ = popt
        ar = abs(ar)
    except:
        # Fallback: use simple max-min
        monthly_means = df.groupby(df['date'].dt.month)['solar'].mean()
        ar = (monthly_means.max() - monthly_means.min()) / 2

    return {
        'rmd': round(rmd, 2),
        'ar': round(ar, 2),
        'rmw': round(rmw, 2)
    }


def main():
    parser = argparse.ArgumentParser(
        description='Estimate WGEN parameters from historical climate data'
    )
    parser.add_argument('--climate', required=True,
                       help='Path to climate CSV file with all variables')
    parser.add_argument('--output-csv', default='wgen_params.csv',
                       help='Output CSV file path for monthly precipitation parameters')
    parser.add_argument('--output-yaml', default='wgen_constants.yaml',
                       help='Output YAML file path for constant parameters')
    parser.add_argument('--latitude', type=float, required=True,
                       help='Station latitude in degrees (-90 to 90)')
    parser.add_argument('--precip-col', default='precip_mm',
                       help='Precipitation column name')
    parser.add_argument('--tmax-col', default='tmax_c',
                       help='Maximum temperature column name')
    parser.add_argument('--tmin-col', default='tmin_c',
                       help='Minimum temperature column name')
    parser.add_argument('--solar-col', default='solar_mjm2',
                       help='Solar radiation column name')
    parser.add_argument('--date-col', default='date',
                       help='Date column name')

    args = parser.parse_args()

    # Validate latitude
    if not -90 <= args.latitude <= 90:
        print(f"Error: Latitude must be between -90 and 90, got {args.latitude}")
        return

    # Load climate data
    print(f"Loading climate data from {args.climate}...")
    climate_df = pd.read_csv(args.climate)

    # Check required columns
    required_cols = [args.date_col, args.precip_col]
    missing_cols = [col for col in required_cols if col not in climate_df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        return

    dates = climate_df[args.date_col]
    precip_series = climate_df[args.precip_col]

    # Estimate precipitation parameters
    print("\nEstimating monthly precipitation parameters...")
    precip_params = estimate_precipitation_params(precip_series, dates)

    # Create DataFrame for CSV output
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    csv_df = pd.DataFrame({
        'Month': months,
        'PWW': precip_params['pww'],
        'PWD': precip_params['pwd'],
        'ALPHA': precip_params['alpha'],
        'BETA': precip_params['beta']
    })

    # Save CSV
    csv_df.to_csv(args.output_csv, index=False)
    print(f"\nMonthly precipitation parameters saved to: {args.output_csv}")
    print("\nEstimated monthly parameters:")
    print(csv_df.to_string(index=False))

    # Estimate temperature and radiation parameters if available
    yaml_params = {'latitude': args.latitude}

    if args.tmax_col in climate_df.columns and args.tmin_col in climate_df.columns:
        print("\nEstimating temperature parameters...")
        tmax_series = climate_df[args.tmax_col]
        tmin_series = climate_df[args.tmin_col]
        temp_params = estimate_temperature_params(tmax_series, tmin_series, precip_series, dates)
        yaml_params.update(temp_params)
    else:
        print(f"\nWarning: Temperature columns not found. Using default values.")
        yaml_params.update({
            'txmd': 20.0, 'atx': 10.0, 'txmw': 18.0,
            'tn': 10.0, 'atn': 8.0,
            'cvtx': 0.02, 'acvtx': -0.01,
            'cvtn': 0.02, 'acvtn': -0.01
        })

    if args.solar_col in climate_df.columns:
        print("Estimating radiation parameters...")
        solar_series = climate_df[args.solar_col]
        rad_params = estimate_radiation_params(solar_series, precip_series, dates)
        yaml_params.update(rad_params)
    else:
        print(f"Warning: Solar radiation column not found. Using default values.")
        yaml_params.update({
            'rmd': 15.0, 'ar': 5.0, 'rmw': 12.0
        })

    # Generate YAML output
    yaml_content = "# WGEN Constant Parameters\n"
    yaml_content += "# Add these to your model configuration YAML file\n\n"
    yaml_content += "wgen_config:\n"
    yaml_content += f"  # Location\n"
    yaml_content += f"  latitude: {yaml_params['latitude']}\n\n"
    yaml_content += f"  # Temperature parameters (Celsius)\n"
    yaml_content += f"  txmd: {yaml_params['txmd']}\n"
    yaml_content += f"  atx: {yaml_params['atx']}\n"
    yaml_content += f"  txmw: {yaml_params['txmw']}\n"
    yaml_content += f"  tn: {yaml_params['tn']}\n"
    yaml_content += f"  atn: {yaml_params['atn']}\n"
    yaml_content += f"  cvtx: {yaml_params['cvtx']}\n"
    yaml_content += f"  acvtx: {yaml_params['acvtx']}\n"
    yaml_content += f"  cvtn: {yaml_params['cvtn']}\n"
    yaml_content += f"  acvtn: {yaml_params['acvtn']}\n\n"
    yaml_content += f"  # Radiation parameters (MJ/m²/day)\n"
    yaml_content += f"  rmd: {yaml_params['rmd']}\n"
    yaml_content += f"  ar: {yaml_params['ar']}\n"
    yaml_content += f"  rmw: {yaml_params['rmw']}\n"

    # Save YAML
    with open(args.output_yaml, 'w') as f:
        f.write(yaml_content)

    print(f"\nConstant parameters saved to: {args.output_yaml}")
    print("\nYAML snippet:")
    print(yaml_content)

    print("\n" + "="*60)
    print("IMPORTANT: Validation checklist")
    print("="*60)
    print("✓ Beta values are 5-25 mm for typical climates")
    print("✓ Mean precip per wet day (alpha × beta) is 3-20 mm")
    print("✓ Probabilities (PWW, PWD) are between 0 and 1")
    print("✓ CSV file has exactly 12 rows")
    print("✓ Latitude is between -90 and 90 degrees")
    print("\nNext steps:")
    print(f"1. Review {args.output_csv} for monthly precipitation parameters")
    print(f"2. Add constants from {args.output_yaml} to your model configuration")
    print(f"3. Reference the CSV file in your YAML: param_file: '{args.output_csv}'")


if __name__ == '__main__':
    main()
