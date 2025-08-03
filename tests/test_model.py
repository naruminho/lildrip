import pandas as pd

from pathlib import Path
import sys

# Allow importing ``lildrip`` when the package has not been installed.  This
# keeps the example easy to run for new contributors.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


from lildrip import BartlettLewisModel


def test_generate_synthetic_rainfall_length():
    model = BartlettLewisModel(
        params={'lambda': 1, 'beta': 1, 'gamma': 1, 'eta': 1, 'mu': 1}
    )
    model.calibrated = True
    rain = model.generate_synthetic_rainfall(
        total_duration_minutes=60, output_interval_minutes=10, seed=0
    )
    assert len(rain) == 6


def test_disaggregate_preserves_total():
    model = BartlettLewisModel(
        params={'lambda': 1, 'beta': 1, 'gamma': 1, 'eta': 1, 'mu': 1}
    )
    model.calibrated = True
    coarse = pd.Series([0, 5], index=pd.date_range('2023-01-01', periods=2, freq='1H'))
    fine = model.disaggregate(coarse, fine_interval_minutes=30, seed=0)
    assert len(fine) == 4
    assert abs(fine.sum() - coarse.sum()) < 1e-6


def test_calibrate_uses_beta_eta_extraction():
    model = BartlettLewisModel()
    event1 = pd.DataFrame(
        {'rainfall_mm': [1, 0, 1]},
        index=pd.date_range('2023-01-01', periods=3, freq='10min'),
    )
    event2 = pd.DataFrame(
        {'rainfall_mm': [2, 0, 0, 3]},
        index=pd.date_range('2023-01-02', periods=4, freq='10min'),
    )
    beta, eta = model.extract_beta_eta(
        [event1, event2], interval_minutes=10, intra_event_gap_minutes=10
    )
    assert beta == 2
    assert eta == 0.1
    params = model.calibrate(
        [event1, event2],
        interval_minutes=10,
        default_beta=None,
        default_eta=None,
        intra_event_gap_minutes=10,
    )
    assert params['beta'] == beta
    assert params['eta'] == eta
