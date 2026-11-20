---
trigger: always_on
---

# Gateway engine and containers

- Treat `engine/templates/` and `engine/lua/nxguard/` as source files for gateway
  configuration. `engine/render.py` coordinates rendering; do not edit generated
  runtime files as the source of truth.
- Check the versions in `Dockerfile` and `packages/` before using NGINX, OpenResty,
  LuaJIT, ModSecurity, or CRS features.
- When changing ModSecurity rules, follow the ID ranges documented in `README.md`
  and check for collisions. Consider rule scope, false positives, and availability.
- The Docker build has separate engine, frontend, and backend stages. Keep related
  scripts, dependency manifests, and RPM specifications consistent.
- Validate the generated configuration with the relevant engine tools when available.
  If runtime validation is unavailable, state that explicitly; textual inspection
  alone is not an engine test.
- Use a local development environment for validation. Do not publish images or apply
  configuration to shared or production environments without explicit authorization.
