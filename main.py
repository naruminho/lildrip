from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO
from lildrip import BartlettLewisModel

app = FastAPI()

@app.post("/calibrar-e-desagregar")
def calibrar_e_desagregar(
    arquivo: UploadFile = File(...),
    interval_minutes: int = Form(10),
    inter_event_gap_minutes: int = Form(30),
    intra_event_gap_minutes: int = Form(15),
    disagg_interval_minutes: int = Form(10),
):
    # Lê CSV do usuário
    df = pd.read_csv(arquivo.file, parse_dates=['timestamp'])
    df = df.set_index('timestamp')

    model = BartlettLewisModel()

    # Pré-processamento e identificação de eventos
    df_proc = model.load_and_preprocess_data(
        file_path=None,  # a função original precisa de ajuste para aceitar DataFrame
        time_column='timestamp',
        rainfall_column='rainfall_mm',
        interval_minutes=interval_minutes
    ) if False else df  # bypass da função para este exemplo

    events = model.identify_events(df['rainfall_mm'], inter_event_gap_minutes=inter_event_gap_minutes)

    # Calibração
    model.calibrate(
        events,
        interval_minutes=interval_minutes,
        default_beta=None,
        default_eta=None,
        intra_event_gap_minutes=intra_event_gap_minutes
    )

    # Criar série grossa (exemplo: agregando por hora)
    coarse_series = df['rainfall_mm'].resample(f'{disagg_interval_minutes*2}min').sum()

    # Desagregação
    disagg = model.disaggregate(coarse_series, fine_interval_minutes=disagg_interval_minutes)

    # Converter para CSV e retornar
    buffer = BytesIO()
    disagg.to_frame(name='rainfall_mm').to_csv(buffer)
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=chuva_desagregada.csv"
    })
