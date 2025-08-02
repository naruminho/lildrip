import pandas as pd
from blm import BartlettLewisModel


def load_dataframe(filepath, index_col='timestamp'):
    """Load a CSV file as a DataFrame with datetime index."""
    try:
        df = pd.read_csv(filepath, parse_dates=[index_col])
        df = df.set_index(index_col)
        return df
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        raise


def main():
    # Load fine resolution rainfall series
    df_fine = load_dataframe('chuva_fina_exemplo.csv')

    # Instantiate model
    bl_model = BartlettLewisModel()

    # Preprocess data
    df_fine_proc = bl_model.load_and_preprocess_data(
        file_path='chuva_fina_exemplo.csv',
        time_column='timestamp',
        rainfall_column='chuva_mm',
        interval_minutes=10
    )

    # Identify events
    events = bl_model.identify_events(df_fine_proc['rainfall_mm'], inter_event_gap_minutes=30)

    # Calibrate model
    params = bl_model.calibrate(events)
    print("Calibrated parameters:", params)

    # Export parameters
    bl_model.export_params('params_calibrados.yaml')

    # Simulate synthetic series (e.g.: 1 day)
    synthetic_rain = bl_model.generate_synthetic_rainfall(
        total_duration_minutes=1440,
        output_interval_minutes=10,
        seed=42
    )
    synthetic_rain.to_csv('chuva_sintetica.csv')
    print("Synthetic rainfall generated and saved.")

    # Load coarse resolution rainfall series
    df_coarse = load_dataframe('chuva_grossa_exemplo.csv')
    coarse_series = df_coarse['chuva_mm_grossa']

    # Disaggregate series
    disaggregated_rain = bl_model.disaggregate(
        coarse_series,
        fine_interval_minutes=10,
        seed=42
    )
    disaggregated_rain.to_csv('chuva_desagregada.csv')
    print("Disaggregated rainfall saved.")

    # Compare with original series (if available)
    start, end = disaggregated_rain.index.min(), disaggregated_rain.index.max()
    original_subset = df_fine_proc['rainfall_mm'].loc[start:end]

    bl_model.plot_comparison_barras(
        original_subset,
        disaggregated_rain,
        title="Original vs Disaggregated"
    )


if __name__ == "__main__":
    main()
