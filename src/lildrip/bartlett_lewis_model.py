import pandas as pd
import numpy as np
from scipy.stats import poisson, expon
import yaml

class BartlettLewisModel:
    def __init__(self, params=None):
        """
        Initialize the Bartlett-Lewis model.
        Args:
            params (dict, optional): Model parameters.
        """
        self.params = params
        self.calibrated = bool(params)

    def load_and_preprocess_data(self, file_path, time_column, rainfall_column, interval_minutes=10, fill_method='zero'):
        """
        Load and preprocess rainfall data from a CSV file.
        Args:
            file_path (str): Path to the CSV file.
            time_column (str): Name of the datetime column.
            rainfall_column (str): Name of the rainfall column.
            interval_minutes (int): Time interval in minutes.
            fill_method (str): 'zero' to fill missing with 0, 'drop' to drop missing.
        Returns:
            pd.DataFrame: Preprocessed rainfall data.
        """
        df = pd.read_csv(file_path, parse_dates=[time_column])
        df = df.set_index(time_column)[[rainfall_column]]
        df.columns = ['rainfall_mm']

        if fill_method == 'zero':
            df = df.asfreq(f'{interval_minutes}min', fill_value=0)
        elif fill_method == 'drop':
            df = df.asfreq(f'{interval_minutes}min').dropna()
        else:
            raise ValueError("fill_method must be 'zero' or 'drop'")

        return df

    def identify_events(self, rainfall_series, inter_event_gap_minutes=30):
        """
        Identify rainfall events based on a minimum dry period (inter_event_gap).
        Args:
            rainfall_series (pd.Series): Rainfall time series.
            inter_event_gap_minutes (int): Minimum dry period between events.
        Returns:
            list of pd.DataFrame: List of rainfall events.
        """
        events = []
        interval_minutes = (rainfall_series.index[1] - rainfall_series.index[0]).total_seconds() / 60
        gap_intervals = int(inter_event_gap_minutes / interval_minutes)
        padded_series = pd.concat([
            pd.Series([0] * gap_intervals, index=pd.date_range(
                start=rainfall_series.index[0] - pd.Timedelta(minutes=gap_intervals * interval_minutes),
                periods=gap_intervals, freq=f'{interval_minutes}min')),
            rainfall_series,
            pd.Series([0] * gap_intervals, index=pd.date_range(
                start=rainfall_series.index[-1] + pd.Timedelta(minutes=interval_minutes),
                periods=gap_intervals, freq=f'{interval_minutes}min'))
        ])
        in_event = False
        dry_spell_counter = 0
        event_start_idx = -1

        for i, value in enumerate(padded_series):
            if value > 0:
                if not in_event:
                    in_event = True
                    event_start_idx = i
                dry_spell_counter = 0
            else:
                dry_spell_counter += 1
                if in_event and dry_spell_counter >= gap_intervals:
                    event_end_idx = i - gap_intervals
                    event = padded_series.iloc[event_start_idx:event_end_idx + 1].loc[lambda x: x > 0]
                    if not event.empty and event.sum() > 0:
                        events.append(event.to_frame(name='rainfall_mm'))
                    in_event = False
                    dry_spell_counter = 0

        return events

    def calibrate(self, events, interval_minutes=10, default_beta=5.0, default_eta=1/10.0):
        """
        Calibrate model parameters using the Method of Moments.
        Args:
            events (list): List of rainfall events.
            interval_minutes (int): Time interval in minutes.
            default_beta (float): Default beta value.
            default_eta (float): Default eta value.
        Returns:
            dict: Calibrated parameters.
        """
        if not events:
            raise ValueError("No rainfall events found for calibration.")

        durations = [len(e) * interval_minutes for e in events]
        intensities = [
            e['rainfall_mm'].sum() / (len(e) * interval_minutes) if len(e) > 0 else 0
            for e in events
        ]
        total_duration_minutes = (events[-1].index[-1] - events[0].index[0]).total_seconds() / 60 or 1

        lambda_param = len(events) / (total_duration_minutes / (24 * 60))
        gamma_param = 1.0 / np.mean(durations) if np.mean(durations) > 0 else 0.01
        mu_param = np.mean(intensities) if np.mean(intensities) > 0 else 0.1

        self.params = {
            'lambda': lambda_param,
            'beta': default_beta,
            'gamma': gamma_param,
            'eta': default_eta,
            'mu': mu_param
        }
        self.calibrated = True
        return self.params

    def generate_synthetic_rainfall(self, total_duration_minutes, output_interval_minutes=10, seed=None):
        """
        Generate a synthetic rainfall time series using the Bartlett-Lewis model.
        Args:
            total_duration_minutes (int): Total duration in minutes.
            output_interval_minutes (int): Output interval in minutes.
            seed (int, optional): Random seed.
        Returns:
            pd.Series: Synthetic rainfall series.
        """
        if not self.calibrated:
            raise ValueError("Model must be calibrated first.")
        if seed is not None:
            np.random.seed(seed)

        p = self.params
        n_intervals = total_duration_minutes // output_interval_minutes
        rainfall = pd.Series(0.0, index=pd.date_range("2000-01-01", periods=n_intervals, freq=f'{output_interval_minutes}min'))

        lambda_per_min = p['lambda'] / (24 * 60)
        n_storms = poisson.rvs(lambda_per_min * total_duration_minutes)

        for _ in range(n_storms):
            storm_start = np.random.uniform(0, total_duration_minutes)
            pulses = poisson.rvs(p['beta'])
            current_time = storm_start
            for _ in range(pulses):
                current_time += expon.rvs(scale=1 / p['gamma'])
                duration = expon.rvs(scale=1 / p['eta'])
                intensity = expon.rvs(scale=p['mu'])

                i_start = int(current_time // output_interval_minutes)
                i_end = int((current_time + duration) // output_interval_minutes)
                for i in range(i_start, i_end):
                    if 0 <= i < len(rainfall):
                        rainfall.iloc[i] += intensity

        return rainfall

    def disaggregate(self, coarse_series, fine_interval_minutes=10, seed=None):
        """
        Disaggregate a coarse rainfall series into a finer resolution using the model.
        Args:
            coarse_series (pd.Series): Coarse rainfall series.
            fine_interval_minutes (int): Fine interval in minutes.
            seed (int, optional): Random seed.
        Returns:
            pd.Series: Disaggregated rainfall series.
        """
        if not self.calibrated:
            raise ValueError("Model must be calibrated first.")
        disagg = pd.Series(dtype=float)

        if len(coarse_series) > 1:
            coarse_interval_minutes = (coarse_series.index[1] - coarse_series.index[0]).total_seconds() / 60
        else:
            coarse_interval_minutes = 60

        for ts, value in coarse_series.items():
            fine_times = pd.date_range(
                start=ts,
                periods=int(coarse_interval_minutes / fine_interval_minutes),
                freq=f'{fine_interval_minutes}min'
            )

            if value == 0:
                new_segment = pd.Series(0.0, index=fine_times)
            else:
                sim = self.generate_synthetic_rainfall(
                    int(coarse_interval_minutes),
                    output_interval_minutes=fine_interval_minutes,
                    seed=seed
                )
                if sim.sum() > 0:
                    sim *= (value / sim.sum())
                else:
                    sim[:] = value / len(sim)
                sim.index = fine_times
                new_segment = sim

            if disagg.empty:
                disagg = new_segment
            else:
                disagg = pd.concat([disagg, new_segment])

        return disagg

    def export_params(self, path='params.yaml'):
        """
        Export calibrated parameters to a YAML file.
        Args:
            path (str): Output file path.
        """
        if not self.params:
            raise ValueError("No calibrated parameters to export.")
        safe_params = {k: float(v) for k, v in self.params.items()}
        with open(path, 'w') as f:
            yaml.dump(safe_params, f)

    def load_params(self, path='params.yaml'):
        """
        Load model parameters from a YAML file.
        Args:
            path (str): Path to the YAML file.
        """
        with open(path, 'r') as f:
            self.params = yaml.safe_load(f)
            self.calibrated = True

import pandas as pd
import numpy as np

def extrair_beta_eta(events, interval_minutes=10, intra_event_gap_minutes=15):
    """
    Automatically extracts beta (avg. pulses per event) and eta (1 / avg. pulse duration)
    by analyzing intra-event dry gaps to identify pulses.

    Args:
        events (list of pd.DataFrame): List of rainfall events.
        interval_minutes (int): Temporal resolution of the rainfall series.
        intra_event_gap_minutes (int): Minimum dry period to separate pulses within an event.

    Returns:
        tuple: (beta, eta)
            beta: Average number of pulses per event.
            eta: 1 / average duration of pulses (in minutes).
    """
    all_pulses_count = []
    all_pulse_durations = []

    gap_intervals = int(intra_event_gap_minutes / interval_minutes)

    for event in events:
        values = event['rainfall_mm'].values

        pulse_count = 0
        pulse_lengths = []

        i = 0
        while i < len(values):
            if values[i] > 0:
                pulse_length = 1
                zero_counter = 0
                i += 1
                while i < len(values):
                    if values[i] > 0:
                        pulse_length += 1
                        zero_counter = 0
                    else:
                        zero_counter += 1
                        if zero_counter >= gap_intervals:
                            break
                        else:
                            pulse_length += 1
                    i += 1
                pulse_count += 1
                pulse_lengths.append(pulse_length * interval_minutes)
            else:
                i += 1

        if pulse_count > 0:
            all_pulses_count.append(pulse_count)
            all_pulse_durations.extend(pulse_lengths)

    beta = np.mean(all_pulses_count) if all_pulses_count else 1.0
    mean_pulse_duration = np.mean(all_pulse_durations) if all_pulse_durations else 10.0
    eta = 1.0 / mean_pulse_duration if mean_pulse_duration > 0 else 0.1

    return beta, eta
