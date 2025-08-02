Modelo Bartlett-Lewis para Desagregação Estocástica de Chuvas
--------------------------------------------------------------

Este modelo implementa a lógica estocástica do processo Bartlett-Lewis para simular a estrutura temporal da precipitação
e realizar a desagregação de séries de chuva com resolução temporal mais grossa (como diária ou horária) para séries mais finas (como 10 min).

Parâmetros do Modelo (calibrados com base em uma série de chuva de alta resolução):
- lambda (λ): frequência média de ocorrência de tempestades (eventos de chuva) por dia.
- beta (β): número médio de pulsos (pequenos eventos de chuva) por tempestade.
- gamma (γ): taxa de término da tempestade (inverso da duração média do evento de chuva).
- eta (η): taxa de término de um pulso (inverso da duração média do pulso de chuva).
- mu (μ): intensidade média da chuva por pulso (mm).

Fluxo de uso:
-------------
1. **Calibração do Modelo**
    - Carregar série de chuva fina com resolução fixa (ex: 10 minutos).
    - Identificar eventos de chuva com base em um tempo seco mínimo entre eles (inter_event_gap).
    - Calibrar os parâmetros do modelo com base nas estatísticas desses eventos.

2. **Desagregação**
    - Carregar série de chuva grossa (ex: horária).
    - Para cada valor observado na série grossa:
        - Simular um evento de chuva com base nos parâmetros calibrados.
        - Ajustar a intensidade da chuva simulada para igualar o volume observado.
        - Dividir a chuva simulada nos intervalos mais finos desejados.

3. **Exportação e Validação**
    - Exportar os parâmetros calibrados em formato YAML para reuso.
    - Comparar visualmente e estatisticamente as séries desagregadas com dados reais (quando disponíveis).

Observações:
------------
- A calibração dos parâmetros usa o Método dos Momentos (MoM), que é mais simples que o MLE, porém mais direto.
- A desagregação é estocástica: cada execução pode gerar uma distribuição diferente para o mesmo valor de entrada.
- É recomendável usar uma semente aleatória (seed) para garantir reprodutibilidade dos resultados.
- O modelo é adequado para aplicações hidrológicas onde a distribuição temporal da chuva afeta escoamento, infiltração, entre outros processos.

Exemplo de Parâmetros Calibrados:
---------------------------------
lambda: 17.5        # ~17 eventos de chuva por dia
beta: 5.0           # ~5 pulsos por evento
gamma: 0.05         # ~20 minutos de duração por evento
eta: 0.1            # ~10 minutos por pulso
mu: 0.12            # ~0.12 mm por pulso de chuva