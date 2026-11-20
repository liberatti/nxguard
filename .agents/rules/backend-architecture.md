---
trigger: always_on
---

# Backend architecture

The backend is organized around these responsibilities:

| Layer | Responsibility |
|---|---|
| `api/controller/` | HTTP endpoints, request validation, authentication, and responses |
| `api/model/` | Marshmallow schemas, DTOs, enums, and data validation |
| `api/repository/` | DuckDB queries, persistence, and schema creation |
| `api/services/` | Business workflows and external integrations |
| `api/tools/` | Operational utilities, scheduled work, and background tasks |

## Dependency boundaries

- Controllers may depend on models, repositories, services, and tools.
- Services may depend on models and repositories.
- Tools may depend on models, repositories, and services.
- Repositories may depend on models and the shared DuckDB repository implementation.
- Models must not depend on controllers, services, or tools.
- Keep dependencies directed toward lower-level layers; avoid circular imports.
- Declare Python imports at module scope. Do not import inside functions, methods,
  loops, or conditional blocks.

## Layer-specific guidance

- Validate and deserialize HTTP input with existing schemas. Keep HTTP status codes
  and response shapes consistent with neighboring endpoints.
- Keep SQL and persistence in repositories. Use the existing `DuckDAO` implementation
  in `api/middleware/repository/duck_db.py`; repositories must not access Flask
  request state.
- Keep schemas free of SQL, database connections, network calls, and other I/O.
- Keep business logic and integration orchestration in services, not controllers.
- Make scheduled and operational tasks safe to retry where practical, and use the
  repository's logging conventions when reporting failures.
- Keep configuration in the existing configuration and environment-variable paths;
  never hardcode credentials or deployment-specific values.
