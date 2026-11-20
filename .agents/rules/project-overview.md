---
trigger: always_on
---

# NXGuard project overview and validation

## Technology

- Backend: Python, Flask, Flask-RESTful, Marshmallow, and Flask-SocketIO.
- Storage and observability: DuckDB and Elasticsearch.
- Frontend: Angular standalone components, TypeScript, Angular Material, RxJS, and
  `@ngx-translate/core`.
- Gateway: NGINX, OpenResty/LuaJIT, ModSecurity v3, and OWASP CRS.
- Packaging: multi-stage Docker builds on Rocky Linux, producing RPM packages.

Check the repository manifests for the versions and commands in use. Do not assume
that a feature in the latest upstream release is supported by this project.

## Validation

- For frontend changes, run `npm run build` from `web/`.
- For backend changes, run relevant checks and tests that already exist. No Python
  test suite or lint command is currently configured in the repository.
- For engine and packaging changes, validate the affected Docker stage when the
  environment allows it. State any validation that was not performed.
- Prefer focused tests and preserve existing behavior. Do not add tooling unless the
  task requires it.

Follow `backend-architecture.md` for backend work, `frontend-guidelines.md` and
`internationalization.md` for UI work, and `secure-development.md` for security-
sensitive changes. Preserve API contracts when a change spans backend and frontend.
