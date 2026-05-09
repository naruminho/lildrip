# lildrip — Bartlett-Lewis Rainfall Disaggregation

[![PyPI version](https://img.shields.io/pypi/v/lildrip)](https://pypi.org/project/lildrip/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)

Stochastic simulation and temporal disaggregation of rainfall using the
**Bartlett-Lewis process**.  It takes coarse-resolution rainfall series (e.g.,
hourly) and generates finer-resolution series (e.g., 10-minute intervals) based
on calibrated storm statistics.

## Quick install

```bash
pip install lildrip
```

For the FastAPI web API:

```bash
pip install "lildrip[api]"
```

## Usage — Python library

```python
from lildrip import BartlettLewisModel

# 1. Calibrate from a fine-resolution CSV
model = BartlettLewisModel()
events = model.identify_events(fine_series, inter_event_gap_minutes=30)
params = model.calibrate(events)
print("Calibrated parameters:", params)

# 2. Disaggregate a coarse series
disagg = model.disaggregate(coarse_series, fine_interval_minutes=10)
```

## Usage — Web API

Start the server:

```bash
pip install "lildrip[api]"
uvicorn app:app --host 0.0.0.0 --port 8000
```

### `POST /calibrar`

Upload a high-resolution CSV to calibrate model parameters.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `arquivo` | file | — | CSV with time and rainfall columns |
| `time_column` | string | `timestamp` | Name of the datetime column |
| `rainfall_column` | string | `rainfall_mm` | Name of the rainfall column |
| `interval_minutes` | int | `10` | Temporal resolution of the series |
| `inter_event_gap_minutes` | int | `30` | Minimum dry period between events |
| `intra_event_gap_minutes` | int | `15` | Minimum dry period between pulses |

### `POST /desagregar`

Upload a coarse CSV + calibration parameters to obtain a disaggregated series.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `arquivo` | file | — | CSV with coarse rainfall |
| `params` | string | — | JSON string of calibration parameters |
| `time_column` | string | `timestamp` | Name of the datetime column |
| `rainfall_column` | string | `rainfall_mm` | Name of the rainfall column |
| `disagg_interval_minutes` | int | `10` | Target fine resolution |

## Running the demo

### No rainfall data? Generate synthetic data first

```bash
python examples/generate_demo_rain.py
```

Creates two sample CSV files:
- `fine_rainfall_demo.csv` — 10-minute resolution (simulated)
- `coarse_rainfall_demo.csv` — hourly aggregate of the same data

### Run the full pipeline (calibrate + disaggregate + plot)

```bash
python examples/bartlett_lewis_demo.py
```

This will:
1. Load the generated fine and coarse data
2. Identify rainfall events and calibrate the model
3. Generate a synthetic series from the calibrated model
4. Disaggregate the coarse series into 10-minute resolution
5. Save all outputs as CSV files
6. Show a comparison plot (saved as `rainfall_comparison_bars.png`)

## Model parameters

The Bartlett-Lewis model describes rainfall through five parameters:

| Symbol | Name | Meaning |
|--------|------|---------|
| λ (lambda) | Storm frequency | Average number of storms per day |
| β (beta) | Pulses per storm | Average number of rain pulses in each storm |
| γ (gamma) | Storm termination rate | Inverse of the average storm duration (min⁻¹) |
| η (eta) | Pulse termination rate | Inverse of the average pulse duration (min⁻¹) |
| μ (mu) | Pulse intensity | Average rainfall intensity per pulse (mm) |

Calibration uses the **Method of Moments (MoM)**.

## Running with Docker

```bash
docker build -t lildrip .
docker run -p 8000:8000 lildrip
```

## Project structure

```
lildrip/
├── src/lildrip/
│   ├── __init__.py
│   ├── bartlett_lewis_model.py   # Core model
│   └── plotting.py               # Visualisation helpers
├── examples/
│   ├── generate_demo_rain.py
│   └── bartlett_lewis_demo.py
├── tests/
│   └── test_model.py
├── app.py                        # FastAPI application
├── main.py                       # Uvicorn entry point
├── Dockerfile
├── pyproject.toml
└── README.md
```

## License

MIT
