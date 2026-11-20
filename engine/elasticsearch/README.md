# Elasticsearch & Kibana Seed Assets

Este diretório contém os arquivos JSON e NDJSON de inicialização (seeds) para o **Elasticsearch** e **Kibana** utilizados pelo NxGuard para armazenamento e visualização de transações HTTP/WAF.

---

## 📁 Estrutura de Arquivos

```text
engine/elasticsearch/
├── index_template.json           # Template composable do índice (_index_template/nxguard_trn_template)
├── index_settings.json           # Definição isolada de settings (shards, replicas, refresh)
├── index_mappings.json           # Definição isolada de mappings dos campos
└── dashboards/
    └── dashboards_export.ndjson  # Pacote consolidado NDJSON com visualizações, buscas e dashboards:
                                  #  1. NxGuard - [Logs] Web Traffic
                                  #  2. NxGuard - [Security] Inspection, GeoIP & RBL Intelligence
                                  #  3. NxGuard - [Transactions] Raw Events Stream
```

---

## 🚀 Como Aplicar os Seeds

### 1. Elasticsearch (Cluster / Engine na porta `9200`)

#### A) Criar o Index Template Composable (Elasticsearch 7.8+ / 8.x):
```bash
curl -X PUT "http://localhost:9200/_index_template/nxguard_trn_template" \
  -H "Content-Type: application/json" \
  -d @index_template.json
```

#### B) Criar um Índice Inicial Diretamente:
```bash
curl -X PUT "http://localhost:9200/nxguard_trn-$(date +%Y.%m.%d)" \
  -H "Content-Type: application/json" \
  -d '{
    "settings": '"$(cat index_settings.json)"',
    "mappings": '"$(cat index_mappings.json)"'
  }'
```

---

## 📊 2. Kibana (Interface / Saved Objects na porta `5601`)

### Opção A: Importação com 1 Clique via UI do Kibana (Recomendado)
1. Acesse o Kibana em `http://localhost:5601`.
2. Vá em **Stack Management** > **Saved Objects**.
3. Clique em **Import** no canto superior direito.
4. Selecione o arquivo `dashboards/dashboards_export.ndjson`.
5. Marque a opção de sobrescrever conflitos (*Automatically overwrite existing objects*) e confirme.

### Opção B: Importação via API cURL do arquivo NDJSON
```bash
curl -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
  -H "kbn-xsrf: true" \
  --form file=@dashboards/dashboards_export.ndjson
```

### Opção C: Importação Individual via REST API

#### 1. Index Pattern / Data View:
```bash
curl -X POST "http://localhost:5601/api/saved_objects/index-pattern/nxguard_trn?overwrite=true" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d @dashboards/index_pattern.json
```

#### 2. Visualizações (Exemplo Unique Visitors):
```bash
curl -X POST "http://localhost:5601/api/saved_objects/visualization/nxguard_trn_unique_visitors?overwrite=true" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d @dashboards/visualizations/unique_visitors.json
```

#### 3. Dashboard Consolidado:
```bash
curl -X POST "http://localhost:5601/api/saved_objects/dashboard/nxguard_trn_dashboard?overwrite=true" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d @dashboards/dashboard.json
```
