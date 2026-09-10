# OpenSearch & OpenSearch Dashboards Seed Assets

Este diretório contém os arquivos JSON e NDJSON de inicialização (seeds) para o **OpenSearch** e **OpenSearch Dashboards** utilizados pelo NxGuard para armazenamento e visualização de transações HTTP/WAF.

---

## 📁 Estrutura de Arquivos

```text
engine/opensearch/
├── index_template.json           # Template composable do índice (_index_template/nxguard_trn_template)
├── index_settings.json           # Definição isolada de settings (shards, replicas, refresh)
├── index_mappings.json           # Definição isolada de mappings dos campos
└── dashboards/
    ├── dashboards_export.ndjson  # Pacote completo NDJSON com todas as visualizações, index pattern e dashboard
    ├── index_pattern.json        # Saved object do Index Pattern (nxguard_trn*)
    ├── dashboard.json            # Saved object do Dashboard consolidado NxGuard
    └── visualizations/           # Saved objects individuais das 15 visualizações
        ├── unique_visitors.json
        ├── total_requests.json
        ├── total_bytes.json
        ├── avg_duration.json
        ├── timeline_status.json
        ├── response_codes.json
        ├── visitors_map.json
        ├── visitors_by_user_agent.json
        ├── bandwidth_timeline.json
        ├── timeline_action.json
        ├── pie_action.json
        ├── host_visits_bytes_table.json
        ├── top_urls.json
        ├── top_services.json
        └── top_referrers.json
```

---

## 🚀 Como Aplicar os Seeds

### 1. OpenSearch (Cluster / Engine na porta `9200`)

#### A) Criar o Index Template Composable (OpenSearch 1.x / 2.x):
```bash
curl -k -u "admin:NxGuard@2026" -X PUT "https://localhost:9200/_index_template/nxguard_trn_template" \
  -H "Content-Type: application/json" \
  -d @index_template.json
```

#### B) Criar um Índice Inicial Diretamente:
```bash
curl -k -u "admin:NxGuard@2026" -X PUT "https://localhost:9200/nxguard_trn-$(date +%Y.%m.%d)" \
  -H "Content-Type: application/json" \
  -d '{
    "settings": '"$(cat index_settings.json)"',
    "mappings": '"$(cat index_mappings.json)"'
  }'
```

---

## 📊 2. OpenSearch Dashboards (Interface / Saved Objects na porta `5601`)

### Opção A: Importação com 1 Clique via UI do Dashboards (Recomendado)
1. Acesse o OpenSearch Dashboards em `http://localhost:5601`.
2. Vá em **Management** > **Stack Management** > **Saved Objects**.
3. Clique em **Import** no canto superior direito.
4. Selecione o arquivo `dashboards/dashboards_export.ndjson`.
5. Marque a opção de sobrescrever conflitos (*Automatically overwrite existing objects*) e confirme.

### Opção B: Importação via API cURL do arquivo NDJSON
```bash
curl -k -u "admin:NxGuard@2026" -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
  -H "osd-xsrf: true" \
  --form file=@dashboards/dashboards_export.ndjson
```

### Opção C: Importação Individual via REST API

#### 1. Index Pattern:
```bash
curl -k -u "admin:NxGuard@2026" -X POST "http://localhost:5601/api/saved_objects/index-pattern/nxguard_trn?overwrite=true" \
  -H "osd-xsrf: true" \
  -H "Content-Type: application/json" \
  -d @dashboards/index_pattern.json
```

#### 2. Visualizações (Exemplo Unique Visitors):
```bash
curl -k -u "admin:NxGuard@2026" -X POST "http://localhost:5601/api/saved_objects/visualization/nxguard_trn_unique_visitors?overwrite=true" \
  -H "osd-xsrf: true" \
  -H "Content-Type: application/json" \
  -d @dashboards/visualizations/unique_visitors.json
```

#### 3. Dashboard Consolidado:
```bash
curl -k -u "admin:NxGuard@2026" -X POST "http://localhost:5601/api/saved_objects/dashboard/nxguard_trn_dashboard?overwrite=true" \
  -H "osd-xsrf: true" \
  -H "Content-Type: application/json" \
  -d @dashboards/dashboard.json
```
