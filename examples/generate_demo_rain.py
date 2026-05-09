"""Generate synthetic fine and coarse rainfall CSV files for the demo."""

import pandas as pd
import numpy as np

FINE_INTERVAL_MIN = 10
COARSE_INTERVAL_MIN = 60
TOTAL_DURATION_MIN = 1440  # 1 day
N_FINE = TOTAL_DURATION_MIN // FINE_INTERVAL_MIN
N_COARSE = TOTAL_DURATION_MIN // COARSE_INTERVAL_MIN

# Fine timestamps
timestamps_fine = pd.date_range(
    start="2023-01-01 00:00", periods=N_FINE, freq=f"{FINE_INTERVAL_MIN}min"
)

# Fine rainfall with some random pulses
rng = np.random.default_rng(42)
rain_fine = rng.poisson(0.3, size=N_FINE).astype(float)
rain_fine[rain_fine < 1] = 0

# Save fine series
df_fine = pd.DataFrame({"timestamp": timestamps_fine, "rainfall_mm": rain_fine})
df_fine.to_csv("fine_rainfall_demo.csv", index=False)

# Aggregate to coarse
df_fine = df_fine.set_index("timestamp")
df_coarse = (
    df_fine.resample(f"{COARSE_INTERVAL_MIN}min")
    .sum()
    .reset_index()
    .rename(columns={"rainfall_mm": "rainfall_mm"})
)
df_coarse.to_csv("coarse_rainfall_demo.csv", index=False)

print("Generated fine_rainfall_demo.csv and coarse_rainfall_demo.csv")
