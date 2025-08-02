import pandas as pd
import numpy as np

# Simulation parameters
fine_interval_min = 10
coarse_interval_min = 60
total_duration_min = 1440  # 1 day
n_fine = total_duration_min // fine_interval_min
n_coarse = total_duration_min // coarse_interval_min

# Generate fine timestamps
timestamps_fine = pd.date_range(start="2023-01-01 00:00", periods=n_fine, freq=f"{fine_interval_min}min")

# Generate fine rainfall with zeros and some pulses
np.random.seed(42)
rain_fine = np.random.poisson(0.3, size=n_fine).astype(float)
rain_fine[rain_fine < 1] = 0

# Create DataFrame for fine rainfall
df_fine = pd.DataFrame({'timestamp': timestamps_fine, 'chuva_mm': rain_fine})
df_fine.to_csv('chuva_fina_exemplo.csv', index=False)

# Aggregate to generate coarse rainfall
df_fine.set_index('timestamp', inplace=True)
df_coarse = df_fine.resample(f"{coarse_interval_min}min").sum().reset_index()
df_coarse = df_coarse.rename(columns={'chuva_mm': 'chuva_mm_grossa'})
df_coarse.to_csv('chuva_grossa_exemplo.csv', index=False)
