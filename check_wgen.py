import pandas as pd

# Load WGEN parameters
df = pd.read_csv(r'c:\Users\JasonLillywhite\source\repos\waterlib\test_logging\data\wgen_params.csv', comment='#')

# Calculate mean precipitation per wet day
df['mean_precip_per_wet_day_mm'] = df['ALPHA'] * df['BETA']

print('WGEN Parameter Analysis')
print('=' * 80)
print('\nMonthly Parameters:')
print(df[['Month', 'PWW', 'PWD', 'ALPHA', 'BETA', 'mean_precip_per_wet_day_mm']])

print(f'\n\nSummary Statistics:')
print(f'  Average mean precip per wet day: {df["mean_precip_per_wet_day_mm"].mean():.2f} mm')
print(f'  Average PWW (wet->wet): {df["PWW"].mean():.3f}')
print(f'  Average PWD (dry->wet): {df["PWD"].mean():.3f}')

# Estimate monthly precipitation
print('\n\nEstimated Monthly Precipitation:')
for _, row in df.iterrows():
    # Steady-state probability of wet day
    p_wet = row['PWD'] / (1 - row['PWW'] + row['PWD'])
    # Expected days per month
    days_per_month = 30
    # Expected wet days
    wet_days = p_wet * days_per_month
    # Mean precipitation per month
    monthly_precip = wet_days * row['mean_precip_per_wet_day_mm']
    print(f"  Month {int(row['Month']):2d}: {monthly_precip:6.1f} mm  ({p_wet*100:4.1f}% wet days, {wet_days:4.1f} wet days/month)")

# Calculate annual total
annual_precip = sum([
    (row['PWD'] / (1 - row['PWW'] + row['PWD'])) * 30 * row['mean_precip_per_wet_day_mm']
    for _, row in df.iterrows()
])
print(f'\nEstimated annual precipitation: {annual_precip:.0f} mm')
