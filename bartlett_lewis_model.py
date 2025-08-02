import pandas as pd
import numpy as np
from scipy.stats import poisson, expon
import matplotlib.pyplot as plt
import yaml

class BartlettLewisModel:
    def __init__(self, params=None):
        self.params = params
        self.calibrated = bool(params)

    def load_and_preprocess_data(self, file_path, time_column, rainfall_column, interval_minutes=10, fill_method='zero'):
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
        events = []
        interval_minutes = (rainfall_series.index[1] - rainfall_series.index[0]).seconds / 60
        gap_intervals = int(inter_event_gap_minutes / interval_minutes)
        padded_series = pd.concat([
            pd.Series([0] * gap_intervals, index=pd.date_range(start=rainfall_series.index[0] - pd.Timedelta(minutes=gap_intervals * interval_minutes),
                                                               periods=gap_intervals, freq=f'{interval_minutes}min')),
            rainfall_series,
            pd.Series([0] * gap_intervals, index=pd.date_range(start=rainfall_series.index[-1] + pd.Timedelta(minutes=interval_minutes),
                                                               periods=gap_intervals, freq=f'{interval_minutes}min'))
        ])
        in_event, dry_spell_counter, event_start_idx = False, 0, -1

        for i in range(len(padded_series)):
            if padded_series.iloc[i] > 0:
                if not in_event:
                    in_event, event_start_idx = True, i
                dry_spell_counter = 0
            else:
                dry_spell_counter += 1
                if in_event and dry_spell_counter >= gap_intervals:
                    event_end_idx = i - gap_intervals
                    event = padded_series.iloc[event_start_idx:event_end_idx + 1].loc[lambda x: x > 0]
                    if not event.empty and event.sum() > 0:
                        events.append(event.to_frame(name='rainfall_mm'))
                    in_event, dry_spell_counter = False, 0

        return events

    def calibrate(self, events, interval_minutes=10, default_beta=5.0, default_eta=1/10.0):
        if not events:
            raise ValueError("No rainfall events found for calibration.")

        durations = [len(e) * interval_minutes for e in events]
        intensities = [e['rainfall_mm'].sum() / (len(e) * interval_minutes) if len(e) > 0 else 0 for e in events]
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
        if not self.calibrated:
            raise ValueError("Model must be calibrated first.")
        disagg = pd.Series(dtype=float)

        if len(coarse_series) > 1:
            coarse_interval_minutes = (coarse_series.index[1] - coarse_series.index[0]).total_seconds() / 60
        else:
            coarse_interval_minutes = 60

        for ts, value in coarse_series.items():
            fine_times = pd.date_range(start=ts, periods=int(coarse_interval_minutes / fine_interval_minutes), freq=f'{fine_interval_minutes}min')

            if value == 0:
                disagg = pd.concat([disagg, pd.Series(0.0, index=fine_times)])
            else:
                sim = self.generate_synthetic_rainfall(int(coarse_interval_minutes), output_interval_minutes=fine_interval_minutes, seed=seed)
                if sim.sum() > 0:
                    sim *= (value / sim.sum())
                else:
                    sim[:] = value / len(sim)
                sim.index = fine_times
                disagg = pd.concat([disagg, sim])

        return disagg

    def export_params(self, path='params.yaml'):
        if not self.params:
            raise ValueError("Nenhum parâmetro calibrado para exportar.")
        # Converte para float puro do Python
        safe_params = {k: float(v) for k, v in self.params.items()}
        with open(path, 'w') as f:
            yaml.dump(safe_params, f)

    def load_params(self, path='params.yaml'):
        with open(path, 'r') as f:
            self.params = yaml.safe_load(f)
            self.calibrated = True

    def plot_comparison(self, original, desagregada, title='Comparação'):
        plt.figure(figsize=(12, 5))
        plt.plot(original.index, original.values, label='Original', alpha=0.7)
        plt.plot(desagregada.index, desagregada.values, label='Desagregada', alpha=0.7, linestyle='--')
        plt.title(title)
        plt.ylabel("Chuva (mm)")
        plt.xlabel("Tempo")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('comparacao_chuva.png')
        plt.show()
        
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt

    def plot_comparison_barras(self, original, desagregada, title='Comparação - Barras'):
        """
        Plota a comparação entre a série original e a desagregada usando gráfico de barras.

        Args:
            original (pd.Series): Série original de alta resolução.
            desagregada (pd.Series): Série desagregada gerada pelo modelo.
            title (str): Título do gráfico.
        """
        plt.figure(figsize=(14, 6))
        bar_width = (original.index[1] - original.index[0]).total_seconds() / 60

        plt.bar(original.index, original.values, width=bar_width / 1440, label='Original', alpha=0.6, align='center')
        plt.bar(desagregada.index, desagregada.values, width=bar_width / 1440, label='Desagregada', alpha=0.6, align='center')

        plt.title(title)
        plt.xlabel("Tempo")
        plt.ylabel("Chuva (mm)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('comparacao_chuva_barras.png')
        plt.show()
