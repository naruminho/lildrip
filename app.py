"""FastAPI application for lildrip — rainfall calibration and disaggregation API.

Usage
-----
    pip install lildrip[api]
    uvicorn app:app --host 0.0.0.0 --port 8000

Endpoints
---------
- POST /calibrar    — Calibrate model parameters from a high-resolution CSV.
- POST /desagregar  — Disaggregate a coarse CSV using pre-calibrated parameters.
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
import json
from io import BytesIO, StringIO

from lildrip import BartlettLewisModel

app = FastAPI(title="lildrip", version="0.1.0")


def _validate_csv(file: UploadFile) -> None:
    """Check that the uploaded file looks like a CSV."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail=f"Expected a CSV file, got '{file.filename}'",
        )


def _read_csv(file: UploadFile, time_col: str, rain_col: str) -> pd.DataFrame:
    """Read and validate the CSV columns, raising a friendly 400 on failure."""
    try:
        content = file.file.read()
        df = pd.read_csv(BytesIO(content), parse_dates=[time_col])
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse CSV: {exc}",
        ) from exc

    if time_col not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing the time column '{time_col}'. "
                   f"Found columns: {list(df.columns)}",
        )
    if rain_col not in df.columns:
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing the rainfall column '{rain_col}'. "
                   f"Found columns: {list(df.columns)}",
        )
    return df.set_index(time_col)


@app.post("/calibrar")
async def calibrar(
    arquivo: UploadFile = File(...),
    time_column: str = Form("timestamp"),
    rainfall_column: str = Form("rainfall_mm"),
    interval_minutes: int = Form(10),
    inter_event_gap_minutes: int = Form(30),
    intra_event_gap_minutes: int = Form(15),
):
    """Calibrate model parameters from a high-resolution rainfall series.

    The uploaded CSV must contain columns matching ``time_column`` and
    ``rainfall_column`` (defaults: ``timestamp`` and ``rainfall_mm``).

    Returns the calibrated parameters as JSON.
    """
    _validate_csv(arquivo)
    df = _read_csv(arquivo, time_column, rainfall_column)

    model = BartlettLewisModel()
    events = model.identify_events(
        df[rainfall_column], inter_event_gap_minutes=inter_event_gap_minutes
    )

    if not events:
        raise HTTPException(
            status_code=400,
            detail="No rainfall events found in the uploaded data. "
                   "Check the time interval or the rainfall threshold.",
        )

    try:
        params = model.calibrate(
            events,
            interval_minutes=interval_minutes,
            default_beta=None,
            default_eta=None,
            intra_event_gap_minutes=intra_event_gap_minutes,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Calibration failed: {exc}"
        ) from exc

    return params


@app.post("/desagregar")
async def desagregar(
    arquivo: UploadFile = File(...),
    params: str = Form(...),
    time_column: str = Form("timestamp"),
    rainfall_column: str = Form("rainfall_mm"),
    disagg_interval_minutes: int = Form(10),
):
    """Disaggregate a coarse rainfall series using previously calibrated parameters.

    ``params`` must be a JSON string with the calibration parameters obtained
    from ``/calibrar``.  The CSV must contain ``time_column`` and
    ``rainfall_column`` columns.

    Returns a CSV with the disaggregated series.
    """
    _validate_csv(arquivo)
    df = _read_csv(arquivo, time_column, rainfall_column)

    try:
        params_dict = json.loads(params)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON in 'params': {exc}"
        ) from exc

    model = BartlettLewisModel(params=params_dict)
    coarse_series = df[rainfall_column]
    try:
        disagg = model.disaggregate(
            coarse_series, fine_interval_minutes=disagg_interval_minutes
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Disaggregation failed: {exc}"
        ) from exc

    buffer = BytesIO()
    disagg.to_frame(name="rainfall_mm").to_csv(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                "attachment; filename=chuva_desagregada.csv"
            )
        },
    )


# ASGI entry point for Google Cloud Functions (2nd gen) and Uvicorn.
