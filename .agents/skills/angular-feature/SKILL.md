---
name: angular-feature
description: Use when implementing or changing NXGuard Angular screens, components, routes, forms, frontend services, or API integrations.
---

# Implement an Angular feature

1. Read `.agents/rules/frontend-guidelines.md` and
   `.agents/rules/internationalization.md`. Inspect a nearby feature before choosing
   component structure or Angular APIs.
2. Identify affected routes, components, services, models, and translation files.
   Preserve the local patterns for standalone components, Angular Material, RxJS,
   and `@ngx-translate/core`; avoid unrelated migrations.
3. Keep frontend models aligned with API contracts. Handle asynchronous loading,
   errors, empty states, and duplicate submissions consistently with the existing
   flow.
4. Translate visible text and keep `web/assets/i18n/en_US.json` and
   `web/assets/i18n/pt_BR.json` synchronized. Preserve accessibility, keyboard use,
   and responsive behavior.
5. Add focused tests only when the existing setup supports them. Run
   `npm run build` from `web/`; do not assume there is a test script.
6. Review the diff, report the checks performed, and note any validation limits.

Avoid new dependencies, global styles, or UX changes outside the requested scope.
