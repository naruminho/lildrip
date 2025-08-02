import pandas as pd
from blm import BartlettLewisModel  # Supondo que a classe foi salva nesse arquivo

# ========== 1. Carregar série de chuva fina ==========
df_fina = pd.read_csv('chuva_fina_exemplo.csv', parse_dates=['timestamp'])
df_fina = df_fina.set_index('timestamp')

# ========== 2. Instanciar modelo ==========
bl_model = BartlettLewisModel()

# ========== 3. Pré-processar dados ==========
df_fina_proc = bl_model.load_and_preprocess_data(
    file_path='chuva_fina_exemplo.csv',
    time_column='timestamp',
    rainfall_column='chuva_mm',
    interval_minutes=10
)

# ========== 4. Identificar eventos ==========
eventos = bl_model.identify_events(df_fina_proc['rainfall_mm'], inter_event_gap_minutes=30)

# ========== 5. Calibrar modelo ==========
params = bl_model.calibrate(eventos)
print("Parâmetros calibrados:", params)

# ========== 6. Exportar parâmetros ==========
bl_model.export_params('params_calibrados.yaml')

# ========== 7. Simular série sintética (ex: 1 dia) ==========
chuva_sintetica = bl_model.generate_synthetic_rainfall(total_duration_minutes=1440, output_interval_minutes=10, seed=42)
chuva_sintetica.to_csv('chuva_sintetica.csv')
print("Chuva sintética gerada e salva.")

# ========== 8. Carregar série de chuva grossa ==========
df_grossa = pd.read_csv('chuva_grossa_exemplo.csv', parse_dates=['timestamp'])
df_grossa = df_grossa.set_index('timestamp')
serie_grossa = df_grossa['chuva_mm_grossa']

# ========== 9. Desagregar série ==========
chuva_desagregada = bl_model.disaggregate(serie_grossa, fine_interval_minutes=10, seed=42)
chuva_desagregada.to_csv('chuva_desagregada.csv')
print("Chuva desagregada salva.")

# ========== 10. Comparar com série original (se tiver) ==========
# Aqui só um exemplo, usa o mesmo período da desagregada
start = chuva_desagregada.index.min()
end = chuva_desagregada.index.max()
original_subset = df_fina_proc['rainfall_mm'].loc[start:end]

bl_model.plot_comparison_barras(original_subset, chuva_desagregada, title="Original vs Desagregada")
