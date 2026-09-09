---
trigger: always_on
---

# Arquitetura e Estrutura de Camadas do Backend (`api/`)

Este documento define os padrões arquiteturais, limites de responsabilidade e diretrizes de design para as camadas da aplicação backend em `api/`.

---

## 1. Visão Geral das Camadas

```text
api/
├── controller/    # Camada de Entrada HTTP / Endpoints REST
├── model/         # Schemas de Dados, Validação e DTOs (Marshmallow)
├── repository/    # Persistência e Acesso a Dados (DuckDB DAOs)
├── services/      # Lógica de Negócio e Integrações Externas
└── tools/         # Utilitários Operacionais e Background Workers
```

---

## 2. Responsabilidades por Camada

### 2.1. `controller/` (Camada de Interface HTTP)
- **Responsabilidade:** Expor endpoints REST e tratar o ciclo de vida da requisição/resposta HTTP (Flask MethodView / rotas).
- **Diretrizes:**
  - Validar e desserializar parâmetros de entrada (query params, path params, JSON payload) utilizando os schemas da camada `model/`.
  - Autenticar, autorizar e tratar códigos de status HTTP (`200`, `201`, `400`, `401`, `403`, `404`, `500`).
  - Não implementar regras de negócio complexas ou comandos SQL diretos; delegar para `services/` ou `repository/`.
  - Serializar respostas utilizando os schemas de saída correspondentes.

### 2.2. `model/` (Camada de Dados e Schemas)
- **Responsabilidade:** Definição de **Schemas** de validação, serialização e deserialização (Marshmallow / Flask-Marshmallow), DTOs e Enums.
- **Diretrizes:**
  - Conter classes de schema (`*Schema`), validações de campos (`@validates_schema`, `@pre_load`, `@post_load`), formatos e tipos.
  - **Zero Persistência:** Não deve conter comandos SQL, DDLs, instâncias diretas de conexão ou manipulação de banco de dados.
  - Para compatibilidade retroativa, os arquivos de modelo podem reexportar os DAOs correspondentes da camada `repository/`.

### 2.3. `repository/` (Camada de Persistência)
- **Responsabilidade:** Acesso exclusivo ao banco de dados (DuckDB), execução de queries SQL, paginação, filtros e DDLs.
- **Diretrizes:**
  - Todas as classes DAO devem herdar de `DuckDAO` (`api/repository/duck_db.py`).
  - Centralizar a criação e migração de tabelas (`create_schema()`, `ddl()`).
  - Implementar métodos de CRUD padrão (`get_by_id`, `get_all`, `persist`, `update_by_id`, `delete_by_id`) e queries específicas.
  - Mapear dicionários e tipos de dados brutos de/para estruturas consumíveis via hooks `to_dict` e `from_dict`.
  - Não manipular objetos de requisição HTTP (`request`, `jsonify`, etc.).

### 2.4. `services/` (Camada de Negócio e Integrações)
- **Responsabilidade:** Orquestração de regras de negócio, transformações complexas e integrações com serviços externos.
- **Diretrizes:**
  - Integrar com serviços externos (ex.: OpenSearch, ElasticSearch, APIs remotas, DNS, IPXA).
  - Coordenar operações envolvendo múltiplos repositórios ou transações cruzadas.
  - Isolar regras de negócio e algoritmos que não pertencem ao ciclo de vida HTTP nem à persistência pura.

### 2.5. `tools/` (Utilitários e Workers)
- **Responsabilidade:** Utilitários operacionais, rotinas assíncronas, tarefas de manutenção e background jobs.
- **Diretrizes:**
  - Executar tarefas como: rotação e expiração de logs, renovação e emissão de certificados SSL/ACME, backup de configurações e arquivamento de transações.
  - Consumíveis tanto por endpoints sob demanda quanto pelo agendador de tarefas periódicas (`tasks.py`) ou comandos CLI.
  - Manter idempotência e tratamento seguro de falhas com logs estruturados.

---

## 3. Fluxo de Dependências Permitido

```
[controller] ──► [services] ──► [repository] ──► [DuckDB / Banco]
     │                 │              ▲
     │                 ▼              │
     ├───► [repository] ──────────────┤
     │                                │
     ├───► [model (Schemas)] ─────────┘
     │
     └───► [tools] ──► [repository / services]
```

### Regras de Importação:
1. `controller` pode importar de `model`, `repository`, `services` e `tools`.
2. `services` pode importar de `model` e `repository`.
3. `tools` pode importar de `model`, `repository` e `services`.
4. `repository` pode importar de `model` (para schemas) e `repository/duck_db.py`.
5. `model` **NUNCA** deve importar `controller`, `services` ou `tools`.
6. **Zero Dependência Circular:** Nenhuma camada inferior deve depender de uma camada superior.

---

## 4. Boas Práticas e Anti-Padrões

### Anti-Padrões (O Que Evitar):
- **SQL no Controller:** Jamais execute queries SQL diretamente em arquivos de `controller/`.
- **Lógica de Negócio no Model:** Não coloque regras de negócio, chamadas de rede ou I/O dentro dos schemas em `model/`.
- **Tratamento HTTP no Repository:** Nunca acesse `flask.request`, `flask.g` ou lance respostas HTTP a partir de `repository/` ou `services/`.
- **Hardcode de Configuração:** Use sempre `config.py` e variáveis de ambiente centralizadas para caminhos, portas e credenciais.
