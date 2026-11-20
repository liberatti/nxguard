---
name: modsecurity-engine-change
description: Use when changing ModSecurity rules, OWASP CRS integration, NGINX/OpenResty templates, Lua gateway behavior, or rendered gateway configuration.
---

# Change the gateway security engine

Engine changes can affect traffic, availability, and false-positive rates. Keep them
focused and validate them before operational use.

1. Read `.agents/rules/gateway-engine.md` and locate the source in
   `engine/templates/`, `engine/seclang/`, `engine/render.py`, or `lua/nxguard/`.
   Trace related callers and templates; do not edit generated runtime files.
2. Check NGINX, OpenResty/LuaJIT, ModSecurity, and CRS versions in `Dockerfile`,
   `packages/`, and `README.md`. Do not assume newer features are available.
3. For rules, review syntax, scope, phases, actions, IDs, exclusions, and inspection
   levels. Consider false positives and availability as well as detection.
4. Add or adjust focused tests using benign and detection examples in an authorized
   local environment. Never test against third-party targets.
5. When available, validate rendered configuration with the engine tools and build
   the affected Docker stage. If runtime validation is unavailable, say so; a text
   review is not a WAF test.
6. Do not apply configuration, restart shared services, or publish images without
   explicit authorization.
