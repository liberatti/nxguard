# sklearn for alert generation

# Especificação de Indicadores e Dashboards — NXGuard & IPXA

Documento de arquitetura analítica para evolução da telemetria em tempo real (`Security Overview`) e implementação da nova view de inteligência (`Threat Insights`), alinhado ao pipeline de decisão do **NXGuard WAF** (Nginx + ModSecurity v3 + OWASP CRS) e do motor de reputação **IPXA**.

---

## 1. Pipeline de Decisão & Mapeamento de Indicadores

O NXGuard avalia cada transação em camadas sequenciais antes e depois do upstream. Os indicadores abaixo exploram cada etapa desse pipeline:

| Camada / Módulo | Campos no Schema JSON | Indicador / Métrica | Valor Operacional |
| :--- | :--- | :--- | :--- |
| **IPXA Intelligence** | `ipxa` (`cached` / miss), `reputation.action`, `reputation.score`, `reputation.reasons`, `reputation.trusted` | **Taxa de Bloqueio IPXA & Hit Rate de Cache** | Mede a eficácia das RBLs/feeds do IPXA na borda e a eficiência do cache de consulta (`ipxa: "cached"`). |
| **Controle de Borda** | `geoip.action`, `rate_limit.action`, `mtls.enabled`, `mtls.verified` | **Funil de Mitigação Pré-WAF** | Quantifica requisições barradas por GeoIP, Rate Limit ou falha de certificado mTLS antes de acionar regex. |
| **Motor ModSecurity** | `sensor._id`, `sensor.action`, `audit.mode`, `audit.messages[].rule_code`, `score` | **Taxa de Bloqueio CRS & Score de Anomalia** | Avalia a efetividade das políticas aplicadas por sensor (`SENSOR-<id>.policy`) e o volume em `DetectionOnly` vs. `Enabled`. |
| **Inspeção Entrada/Saída** | `audit.messages[].match` (`REQUEST_*` vs. `RESPONSE_BODY`), `upstream.status`, `http.response.status_code` | **Interceptação de Saída (Data Leakage)** | Identifica respostas `200` do upstream bloqueadas na saída (`200 ➔ 403`), diferenciando vazamentos reais de falsos positivos. |
| **Tuning de Políticas** | `route_name`, `http.request.uri`, `audit.messages[].rule_code`, `source.ip` (distinct) | **Índice de Falsos Positivos** | Detecta rotas/assets (ex: `.js.map`) disparando a mesma regra para múltiplos IPs legítimos, gerando insumos para exceções no `.policy`. |
| **Anomalias Silenciosas** | `action == "allowed"` WHERE `score > 0` | **Sondagem Abaixo do Threshold** | Monitora requisições que pontuaram em regras do CRS sem atingir o limite de bloqueio do sensor. |
| **Performance / Latência** | `http.duration`, `http.urt`, `http.uht`, `http.request.bytes`, `http.response.bytes` | **Overhead do NXGuard (ms)** | Isola o custo computacional do WAF (`(http.duration - http.urt) * 1000`) por tamanho de payload e rota. |

---

## 2. Upgrades na View Atual: `Security Overview`

Manter a identidade visual atual focada em **telemetria em tempo real e saúde**, enriquecendo os widgets existentes sem aumentar a poluição visual:

### 2.1. Card `TOTAL REQUESTS`
* **Adição:** Exibir no rodapé do card o **Avg WAF Overhead** (ex: `Overhead: 2.1ms`), calculado via média de `(http.duration - http.urt) * 1000`.

### 2.2. Card `IPXA INTELLIGENCE`
* **Adição:** Exibir um sub-indicador com o **Cache Hit Rate** (`ipxa == "cached"`) e o total de bloqueios preventivos realizados pela camada de reputação (`reputation.action == "blocked"`).

### 2.3. Gráfico `Request Volume`
* **Adição:** Sobrepor uma segunda série (área/linha vermelha discreta na base) com **Blocked Requests/min** (`action == "blocked"`), permitindo correlacionar visualmente picos de acesso com ondas de ataque.

### 2.4. Tabela `Threat Detection Log`
Aproveitar o espaço horizontal entre `EVENT / ROUTE` e `CLIENT IP` para adicionar:
* **Coluna `MODULE / RULE`:** Badge indicando a origem da decisão (`IPXA`, `GeoIP`, `RateLimit`, `mTLS` ou o `rule_code` do ModSecurity, ex: `956100`).
* **Coluna `SCORE / FLOW`:** Score de anomalia (`score`) + transição de status HTTP (`upstream.status` $\rightarrow$ `http.response.status_code`, ex: `200 ➔ 403`).
* **Drawer de Forense (Click na linha):** Painel lateral exibindo:
  * Detalhes do `audit.messages[]` (`data`, `match`, `severity`, `tags`).
  * Motivos de reputação do IPXA (`reputation.reasons` e `reputation.score`).
  * Headers de contexto (`User-Agent`, `Sec-Fetch-*`, `X-Request-Id`).
  * Botão **`Gerar Exceção`** para copiar a diretiva `SecRuleRemoveById` pronta para o arquivo de política do sensor (`/opt/nxguard/modsec/coreruleset/SENSOR-<id>.policy`).

---

## 3. Nova View: `Threat Insights` (Menu Lateral)

Adicionar o item **Threat Insights** no menu lateral (logo abaixo de `Dashboard`), seguindo o design system atual (cards brancos, bordas suaves, badges pastéis e tipografia limpa).

### Barra Superior de Filtros Globais
* **Período (`logtime`):** `15m`, `1h`, `24h`, `7d`, customizado.
* **Serviço / Rota:** `service.name` e `route_name`.
* **Sensor / Política:** `sensor.name` (`default_7`, etc.) e `audit.mode` (`Enabled` / `DetectionOnly`).
* **Decisão (`action`):** `All`, `Blocked`, `Allowed`.

---

### Linha 1: Funil de Eficiência de Borda (5 Cards / Barras de Proporção)
Exibe a distribuição de bloqueios por etapa do pipeline do NXGuard, evidenciando o alívio de carga sobre o ModSecurity:
1. **IPXA Reputation:** `reputation.action == "blocked"`
2. **GeoIP Filter:** `geoip.action == "blocked"`
3. **Rate Limiting:** `rate_limit.action == "blocked"`
4. **mTLS Enforcement:** `mtls.enabled == true && mtls.verified == false`
5. **OWASP CRS (ModSec):** `audit.mode == "Enabled" && action == "blocked"`

---

### Linha 2: Inteligência de Ameaças (Grid 2 Colunas — 50% / 50%)

#### Esquerda — Categorias OWASP / CAPEC (Gráfico de Barras Horizontais)
* **Fonte:** Agregação das tags `OWASP_CRS/*` em `audit.messages[].tags` (ex: `SQLI`, `XSS`, `DATA-LEAKAGES-RUBY`, `PROTOCOL-ENFORCEMENT`).
* **Objetivo:** Identificar os vetores de ataque mais explorados contra os serviços protegidos.

#### Direita — Top Ofensores & Reputação IPXA (Tabela Compacta)
* **Fonte:** Agrupamento por `source.ip` + `geoip.country_code` + `reputation.score`.
* **Colunas:** `IP / País`, `IPXA Score & Reasons`, `Bloqueios`, `Score Máx. CRS`.
* **Valor:** Permite cruzar IPs já marcados nas RBLs do IPXA com comportamentos anômalos detectados localmente pelo ModSecurity.

---

### Linha 3: Tuning de Sensores & Falsos Positivos (Largura Total — 100%)
Tabela voltada para manutenção das políticas de cada sensor (`SENSOR-<id>.policy`):
* **Agrupamento:** `sensor.name` + `route_name` + `http.request.uri` + `audit.messages[].rule_code`.
* **Colunas:**
  * `Sensor / Rota` (ex: `default_7` • `front-req`)
  * `URI` (ex: `/nxg/styles.js.map`)
  * `Regra & Mensagem` (ex: `956100 — RUBY Information Leakage`)
  * `Fase` (`Request` vs. `Response Body`)
  * `IPs Únicos` (alto número de IPs distintos sinaliza falso positivo de aplicação)
  * `Ocorrências`
  * `Ação`: Botão **`Copiar Regra CRS`** (gera snippet `SecRule REQUEST_URI "@beginsWith ..." "id:...,phase:1,pass,nolog,ctl:ruleRemoveById=956100"`).

---

### Linha 4: Performance & Anomalias Silenciosas (Grid 2 Colunas — 50% / 50%)

#### Esquerda — Overhead de Inspeção por Rota (P95)
* **Fonte:** `route_name`, média de `http.response.bytes` e P95 de `(http.duration - http.urt) * 1000`.
* **Objetivo:** Detectar rotas com respostas volumosas onde o `SecResponseBodyAccess` está adicionando latência desnecessária (ex: bundles JS, sourcemaps, downloads).

#### Direita — Anomalias Silenciosas (`score > 0` com `action == "allowed"`)
* **Fonte:** Requisições permitidas que dispararam regras informativas ou não atingiram o threshold de bloqueio do sensor.
* **Colunas:** `Rota / URI`, `Score`, `Regras Acionadas`, `Ocorrências`.
* **Objetivo:** Antecipar regras ruidosas antes de aumentar o *Paranoia Level* ou detectar reconhecimento lento.

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

Transação de exemplo
{
    "_id": 194,
    "action": "blocked",
    "archived": false,
    "audit": {
        "components": [
            "OWASP_CRS/4.25.1\""
        ],
        "connector": "ModSecurity-nginx v1.0.4",
        "engine": "ModSecurity v3.0.14 (Linux)",
        "messages": [
            {
                "accuracy": "0",
                "data": "Matched Data: RuntimeError: found within RESPONSE_BODY",
                "file": "/opt/nxguard/modsec/coreruleset/SENSOR-default_7.policy",
                "lineNumber": "1277",
                "match": "Matched \"Operator `PmFromFile' with parameter `ruby-errors.data' against variable `RESPONSE_BODY' (Value: `{\"version\":3,\"file\":\"styles.js\",\"mappings\":\";;;;;;;;;AAAY;;AAEZ,MAAM,CAAC,OAAO,GAAG,QAAQ;;AAEzB;AACA (214121 characters omitted)' )",
                "maturity": "0",
                "message": "RUBY Information Leakage",
                "reference": "o128407,13v341,214215",
                "rev": "",
                "ruleId": "956100",
                "rule_code": "956100",
                "severity": "3",
                "tags": [
                    "application-multi",
                    "language-ruby",
                    "platform-multi",
                    "attack-disclosure",
                    "paranoia-level/1",
                    "OWASP_CRS",
                    "OWASP_CRS/DATA-LEAKAGES-RUBY",
                    "capec/1000/118/116"
                ],
                "text": "RUBY Information Leakage",
                "ver": "OWASP_CRS/4.25.1"
            }
        ],
        "mode": "Enabled",
        "rulesets": []
    },
    "destination": {
        "host": "nxguard.local",
        "ip": "172.20.0.3",
        "port": 443
    },
    "geoip": {
        "action": "allowed",
        "country_code": "--"
    },
    "http": {
        "duration": 0.063,
        "referer": "-",
        "request": {
            "bytes": 352,
            "headers": [
                {
                    "content": "nxguard.local:8443",
                    "name": "Host"
                },
                {
                    "content": "no-cors",
                    "name": "Sec-Fetch-Mode"
                },
                {
                    "content": "empty",
                    "name": "Sec-Fetch-Dest"
                },
                {
                    "content": "keep-alive",
                    "name": "Connection"
                },
                {
                    "content": "same-origin",
                    "name": "Sec-Fetch-Site"
                },
                {
                    "content": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/158.0.0.0 Safari/537.36",
                    "name": "User-Agent"
                },
                {
                    "content": "gzip, deflate, br, zstd",
                    "name": "Accept-Encoding"
                },
                {
                    "content": "en-US,en;q=0.9",
                    "name": "Accept-Language"
                }
            ],
            "method": "GET",
            "uri": "/nxg/styles.js.map"
        },
        "request_line": "GET /nxg/styles.js.map HTTP/1.1",
        "response": {
            "bytes": 57751,
            "headers": [
                {
                    "content": "SAMEORIGIN",
                    "name": "X-Frame-Options"
                },
                {
                    "content": "NXGuard",
                    "name": "X-Powered-By"
                },
                {
                    "content": "keep-alive",
                    "name": "Connection"
                },
                {
                    "content": "bytes",
                    "name": "Accept-Ranges"
                },
                {
                    "content": "strict-origin-when-cross-origin",
                    "name": "Referrer-Policy"
                },
                {
                    "content": "1; mode=block",
                    "name": "X-XSS-Protection"
                },
                {
                    "content": "bf7f83b1ba7e9bfa1bbd71a76d3cfe5b",
                    "name": "X-Request-Id"
                },
                {
                    "content": "",
                    "name": "Server"
                },
                {
                    "content": "application/json; charset=utf-8",
                    "name": "Content-Type"
                },
                {
                    "content": "214215",
                    "name": "Content-Length"
                },
                {
                    "content": "Thu, 19 Nov 2026 19:34:40 GMT",
                    "name": "Date"
                },
                {
                    "content": "nosniff",
                    "name": "X-Content-Type-Options"
                },
                {
                    "content": "camera=(), microphone=(), geolocation=()",
                    "name": "Permissions-Policy"
                }
            ],
            "status_code": 200
        },
        "uht": 0.059,
        "urt": 0.063
    },
    "ipxa": "cached",
    "logtime": "2026-11-19T19:34:40.000000Z",
    "mtls": {
        "enabled": true,
        "verified": false
    },
    "rate_limit": {
        "action": "allowed"
    },
    "reputation": {
        "action": "allowed",
        "reasons": {},
        "score": 0,
        "trusted": false
    },
    "route_name": "front-req",
    "score": 4,
    "sensor": {
        "_id": "default_7",
        "action": "allowed",
        "name": "default_7"
    },
    "server_id": "73faf0403b65",
    "service": {
        "_id": "local-dev",
        "name": "local-dev"
    },
    "source": {
        "ip": "172.20.0.1",
        "port": 54010
    },
    "unique_id": "bf7f83b1ba7e9bfa1bbd71a76d3cfe5b",
    "upstream": {
        "name": "NXGuard_Frontend",
        "status": 200,
        "target": "172.17.0.1:4200"
    },
    "user_agent": {
        "family": "Chrome",
        "major": 158,
        "minor": 0
    }
}