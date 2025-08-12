from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import pandas as pd
import json
from io import BytesIO

from lildrip import BartlettLewisModel


app = FastAPI()


@app.post("/calibrar")
async def calibrar(
    arquivo: UploadFile = File(...),
    interval_minutes: int = Form(10),
    inter_event_gap_minutes: int = Form(30),
    intra_event_gap_minutes: int = Form(15),
):
    """Calibrate model parameters from a high-resolution rainfall series.

    The uploaded CSV must contain ``timestamp`` and ``rainfall_mm`` columns.
    The endpoint returns the calibrated parameters in JSON format.
    """
    df = pd.read_csv(arquivo.file, parse_dates=["timestamp"]).set_index("timestamp")

    model = BartlettLewisModel()
    events = model.identify_events(
        df["rainfall_mm"], inter_event_gap_minutes=inter_event_gap_minutes
    )

    params = model.calibrate(
        events,
        interval_minutes=interval_minutes,
        default_beta=None,
        default_eta=None,
        intra_event_gap_minutes=intra_event_gap_minutes,
    )

    return params


@app.post("/desagregar")
async def desagregar(
    arquivo: UploadFile = File(...),
    params: str = Form(...),
    disagg_interval_minutes: int = Form(10),
):
    """Disaggregate a coarse rainfall series using previously calibrated parameters.

    ``params`` must be a JSON string with the calibration parameters obtained
    from ``/calibrar``. The uploaded CSV must contain ``timestamp`` and
    ``rainfall_mm`` columns representing the coarse series to be disaggregated.
    The endpoint returns a CSV file with the disaggregated rainfall series.
    """
    df = pd.read_csv(arquivo.file, parse_dates=["timestamp"]).set_index("timestamp")
    params_dict = json.loads(params)

    model = BartlettLewisModel(params=params_dict)
    coarse_series = df["rainfall_mm"]
    disagg = model.disaggregate(
        coarse_series, fine_interval_minutes=disagg_interval_minutes
    )

    buffer = BytesIO()
    disagg.to_frame(name="rainfall_mm").to_csv(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=chuva_desagregada.csv"},
    )


# The ``app`` object is the ASGI entry point for Google Cloud Functions (2nd gen).

