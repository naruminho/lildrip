# lildrip

*Stochastic rainfall disaggregation with the Bartlett-Lewis process*

[![PyPI](https://img.shields.io/pypi/v/lildrip?color=blue)](https://pypi.org/project/lildrip/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

**lildrip** takes coarse-resolution rainfall data (e.g. hourly) and generates
finer-resolution series (e.g. 10-minute intervals) using the **Bartlett-Lewis
stochastic process** — a well-established model in hydrology.

## Quick start

```bash
pip install lildrip
```

```python
from lildrip import BartlettLewisModel

model = BartlettLewisModel()
events = model.identify_events(fine_series, inter_event_gap_minutes=30)
params = model.calibrate(events)

disagg = model.disaggregate(coarse_series, fine_interval_minutes=10)
```

### Web API

```bash
pip install "lildrip[api]"
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Then `POST /calibrar` with a high-resolution CSV or `POST /desagregar`
with coarse data + pre-calibrated parameters.  Both endpoints accept
configurable column names (`time_column`, `rainfall_column`).

See the [full API docs](#usage--web-api) below.

## Demo

Run the examples from the repository root:

```bash
# No data?  Generate sample CSV files first:
python examples/generate_demo_rain.py

# Full pipeline (calibrate → disaggregate → plot):
python examples/bartlett_lewis_demo.py
```

## Model parameters

The Bartlett-Lewis model describes rainfall through five parameters
calibrated via the **Method of Moments**.

| Parameter | Description                |
|-----------|----------------------------|
| λ (lambda)| Storm frequency (events/day)|
| β (beta)  | Pulses per storm           |
| γ (gamma) | Storm termination rate     |
| η (eta)   | Pulse termination rate     |
| μ (mu)    | Pulse intensity (mm)       |

## Project structure

```
lildrip/
├── src/lildrip/
│   ├── __init__.py
│   ├── bartlett_lewis_model.py   # Core model
│   └── plotting.py               # Visualisation helpers
├── api/
│   ├── app.py                    # FastAPI application
│   └── main.py                   # Uvicorn entry point
├── examples/
│   ├── generate_demo_rain.py     # Generate synthetic data
│   └── bartlett_lewis_demo.py    # Calibrate + disaggregate demo
├── tests/
│   └── test_model.py
├── Dockerfile
├── pyproject.toml
└── README.md
```

## License

[MIT](LICENSE)
