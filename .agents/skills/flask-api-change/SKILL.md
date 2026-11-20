---
name: flask-api-change
description: Use when adding or changing NXGuard Flask endpoints, API contracts, validation, or backend business workflows.
---

# Change the Flask API

1. Read `.agents/rules/backend-architecture.md`. Trace the relevant flow through
   `api/routes.py`, `api/controller/`, `api/model/`, `api/repository/`, and
   `api/services/`.
2. Identify request validation, authentication and authorization, persistence,
   response format, and affected consumers before editing.
3. Keep each responsibility in its appropriate layer. Preserve existing HTTP status
   codes, response shapes, pagination, and serialization conventions.
4. If the API contract changes, update affected frontend models and translations.
5. Add focused tests when a compatible test harness exists. Do not assume pytest or
   a configured Python test suite; do not add test dependencies without need.
6. Review the diff for SQL in controllers, sensitive data in logs, and unrelated
   changes. Run available checks and report what was validated.

Do not restructure layers or change unrelated endpoints.
