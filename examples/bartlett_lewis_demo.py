"""Demonstration script for the Bartlett-Lewis rainfall model.

This script can be executed directly from the repository root without first
installing the ``lildrip`` package.  To achieve this we append the ``src``
directory to ``sys.path`` so the package can be imported when running

``python examples/bartlett_lewis_demo.py``.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from lildrip import BartlettLewisModel, plot_comparison, plot_comparison_bars


def load_dataframe(filepath: str, index_col: str = "timestamp") -> pd.DataFrame:
    """Load a CSV file as a DataFrame with datetime index."""
    df = pd.read_csv(filepath, parse_dates=[index_col])
    return df.set_index(index_col)


def main() -> None:
    # ── 1. Load fine-resolution rainfall ──────────────────────────────
    df_fine = load_dataframe("fine_rainfall_demo.csv")

    bl_model = BartlettLewisModel()

    # Preprocess
    df_fine_proc = bl_model.load_and_preprocess_data(
        file_path="fine_rainfall_demo.csv",
        time_column="timestamp",
        rainfall_column="rainfall_mm",
        interval_minutes=10,
    )

    # ── 2. Identify events and calibrate ──────────────────────────
    events = bl_model.identify_events(
        df_fine_proc["rainfall_mm"], inter_event_gap_minutes=30
    )
    params = bl_model.calibrate(events)
    print("Calibrated parameters:", params)
    bl_model.export_params("calibrated_params.yaml")

    # ── 3. Generate synthetic rainfall (1 day) ────────────────────
    synthetic_rain = bl_model.generate_synthetic_rainfall(
        total_duration_minutes=1440, output_interval_minutes=10, seed=42
    )
    synthetic_rain.to_csv("synthetic_rainfall.csv")
    print("Synthetic rainfall saved to synthetic_rainfall.csv")

    # ── 4. Disaggregate a coarse series ──────────────────────────
    df_coarse = load_dataframe("coarse_rainfall_demo.csv")
    coarse_series = df_coarse["rainfall_mm"]

    disaggregated_rain = bl_model.disaggregate(
        coarse_series, fine_interval_minutes=10, seed=42
    )
    disaggregated_rain.to_csv("disaggregated_rainfall.csv")
    print("Disaggregated rainfall saved to disaggregated_rainfall.csv")

    # ── 5. Visual comparison ──────────────────────────────────────
    start = disaggregated_rain.index.min()
    end = disaggregated_rain.index.max()
    original_subset = df_fine_proc["rainfall_mm"].loc[start:end]

    plot_comparison_bars(original_subset, disaggregated_rain, title="Original vs Disaggregated")


if __name__ == "__main__":
    main()
