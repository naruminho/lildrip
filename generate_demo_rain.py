import pandas as pd
import numpy as np

# Parâmetros da simulação
intervalo_fino_min = 10
intervalo_grosso_min = 60
duracao_total_min = 1440  # 1 dia
n_fino = duracao_total_min // intervalo_fino_min
n_grosso = duracao_total_min // intervalo_grosso_min

# Gerar timestamps
timestamps_finos = pd.date_range(start="2023-01-01 00:00", periods=n_fino, freq=f"{intervalo_fino_min}min")

# Gerar chuva fina com zeros e alguns pulsos
np.random.seed(42)
chuva_fina = np.random.poisson(0.3, size=n_fino).astype(float)
chuva_fina[chuva_fina < 1] = 0

# Criar DataFrame da chuva fina
df_fina = pd.DataFrame({'timestamp': timestamps_finos, 'chuva_mm': chuva_fina})
df_fina.to_csv('chuva_fina_exemplo.csv', index=False)

# Agregar para gerar a chuva grossa
df_fina.set_index('timestamp', inplace=True)
df_grossa = df_fina.resample(f"{intervalo_grosso_min}min").sum().reset_index()
df_grossa = df_grossa.rename(columns={'chuva_mm': 'chuva_mm_grossa'})
df_grossa.to_csv('chuva_grossa_exemplo.csv', index=False)
