---
trigger: always_on
---

# Frontend Architecture & Guidelines (Angular + Material)

## Core Architectural Standards

- **Component Structure:** Enforce strict file separation per component (`.ts`, `.html`, `.css`).
- **Modern Angular Paradigms:** Use standalone components by default, modern control flow (`@if`, `@for`, `@switch`), and Signal-based reactivity where applicable.
- **Component Selection:** Prefer built-in Angular Material components over custom HTML/CSS wrappers. Custom components are only permitted when no Material primitive satisfies the functional requirement.

## Styling & Layout

- **Styling Paradigm:** Use **CSS** exclusively. No inline styles (`style="..."`) under any circumstance.
- **Design Tokens & Theming:**
  - Consume Angular Material M3 tokens (`mat.theme-overrides` / CSS custom properties) for palette, typography, and density.
  - Zero hardcoded hex/rgb colors in component stylesheets.
- **Layout Architecture:**
  - Rely on standard CSS Flexbox/Grid via lightweight utility classes.
  - Do not install or import deprecated layout libraries (e.g., `@angular/flex-layout`).
- **Material Overrides:**
  - Do not use `::ng-deep` or arbitrary `!important` to force style overrides.
  - Apply custom variants exclusively via Material structural APIs or custom utility wrapper classes.

## Responsiveness & Breakpoints

- **Design Strategy:** Mobile-first approach.
- **Breakpoint Handling:** Use Angular CDK's `BreakpointObserver` for dynamic DOM changes, and CSS native `@media` queries matching standard Material breakpoints (`sm`, `md`, `lg`) for layout shifts.

## Visual Identity (Dark & Futuristic)

- **Palette Base:** Dark mode surface hierarchy following M3 elevation layers (`surface-container-low`, `high`, etc.).
- **Accents:** Controlled use of high-contrast primary/accent colors, neon accents, and subtle glow effects (`box-shadow` tokens) applied only to critical interactive states.

## Anti-Patterns & Constraints

- **No CSS Bloat:** Reject extensive component-level stylesheets; leverage host layout properties.
- **No Reinventing the Wheel:** Do not build custom dialogs, tooltips, select dropdowns, or snackbars.
- **Accessibility (a11y):** Never strip default Material focus indicators, ARIA attributes, or keyboard navigation behaviors.