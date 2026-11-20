---
trigger: always_on
---

# Frontend architecture, UX, and accessibility

The frontend uses Angular 22, standalone components, Angular Material, TypeScript,
RxJS, and `@ngx-translate/core`. Follow the conventions of the feature being changed;
do not migrate neighboring code just to adopt a newer style.

## Angular and components

- Keep components focused and organize code by feature.
- Prefer Angular Material and existing shared components over custom replacements.
- Use the Angular APIs and template syntax already established in the relevant area.
- Keep state, subscriptions, and change detection straightforward. Add Signals,
  `OnPush`, or abstractions when they solve a concrete need, not as mechanical
  migrations.
- Preserve API types and handle loading, empty, success, and error states.

## Visual design

- Keep hierarchy, spacing, alignment, typography, and interaction patterns consistent
  with the existing interface.
- Reuse existing theme tokens and Material styling APIs. Avoid arbitrary colors,
  typography, spacing, shadows, and undocumented component selectors.
- Use CSS Grid or Flexbox for layout. Prefer fluid sizing and avoid horizontal
  overflow on small screens.
- Keep component styles scoped. Avoid inline styles, `ngStyle`, `::ng-deep`, and
  unnecessary `!important` declarations.
- Prefer meaningful content grouping over decorative cards, borders, and effects.

## Accessibility and interaction

- Use semantic HTML, accessible names, visible focus states, and keyboard-operable
  interactions. Do not convey state through color alone.
- Preserve usable touch targets and responsive behavior.
- Give clear feedback for asynchronous actions. Keep validation errors near their
  controls and prevent accidental duplicate submissions.
- Confirm destructive actions when appropriate, but avoid unnecessary dialogs.

## Review

Before completing a UI change, check visual consistency, responsive behavior,
keyboard access, loading and error states, and preservation of existing behavior.
Run `npm run build` from `web/`; the frontend currently has no `test` script.
