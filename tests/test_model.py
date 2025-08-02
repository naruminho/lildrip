import pandas as pd

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
