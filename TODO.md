# sklearn for alert generation

```python
import json
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# 1. Carregamento e normalização do JSON aninhado
# Supondo que 'logs' seja a lista de dicts (ou use pd.read_json('logs.json'))
logs = [...]  # Seus logs aqui

df_raw = pd.json_normalize(logs)

# 2. Extração de colunas relevantes
# Mapeia campos principais do payload
df = pd.DataFrame(
    {
        "src_ip": df_raw["source.ip"],
        "action": df_raw["action"],
        "status_code": df_raw["http.response.status_code"],
        "req_bytes": df_raw["http.request.bytes"],
        "duration": df_raw["http.duration"],
        "uri": df_raw["http.request.uri"],
    }
)

# 3. Engenharia de Features por IP (comportamento agregado)
features = (
    df.groupby("src_ip")
    .agg(
        total_requests=("src_ip", "count"),
        deny_count=("action", lambda x: (x == "DENY").sum()),
        deny_ratio=("action", lambda x: (x == "DENY").mean()),
        error_4xx_ratio=(
            "status_code",
            lambda x: ((x >= 400) & (x < 500)).mean(),
        ),
        avg_req_bytes=("req_bytes", "mean"),
        avg_duration=("duration", "mean"),
        unique_uris=("uri", "nunique"),
    )
    .reset_index()
)

# 4. Detecção de Anomalias com Scikit-Learn
X = features.drop(columns=["src_ip"])

# Normalização
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Isolation Forest (ajuste o contamination conforme a proporção esperada de anomalias)
model = IsolationForest(contamination=0.05, random_state=42)
features["anomaly_label"] = model.fit_predict(X_scaled)  # -1 = Anomalia, 1 = Normal
features["anomaly_score"] = model.decision_function(X_scaled)

# 5. Filtrar Atacantes / Suspeitos
suspects = features[features["anomaly_label"] == -1].sort_values(
    by="anomaly_score"
)
print(suspects)
```