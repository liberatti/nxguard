---
trigger: always_on
---

# Frontend Architecture, UX/UI & Design System Guidelines
**Stack: Angular 22 + Angular Material 3**

## 1. Core Principles

Act as a Senior Frontend Engineer with strong UX/UI design expertise.

Every interface must prioritize:

- Visual consistency and design coherence.
- Clear information hierarchy.
- Predictable spacing and alignment.
- Excellent readability and typography.
- Accessibility and usability.
- Responsive behavior across screen sizes.
- Simplicity over unnecessary visual complexity.

Do not treat UI implementation as merely placing components on a screen. Every layout decision must have a clear usability and visual-design purpose.

Prefer established design patterns over arbitrary visual decisions.

## 2. Angular Architecture

- Use Angular 22 and modern Angular APIs.
- Use standalone components by default.
- Prefer Signals for reactive state management where appropriate.
- Use modern template control flow: `@if`, `@for`, and `@switch`.
- Prefer `inject()` over constructor-based dependency injection.
- Use `input()` and `output()` APIs where appropriate.
- Keep components focused on a single responsibility.
- Separate component files into `.ts`, `.html`, and `.css`.
- Organize code by feature and business domain.
- Avoid unnecessary abstractions and deeply nested component hierarchies.
- Use `ChangeDetectionStrategy.OnPush` where applicable.

## 3. Angular Material Standards

Angular Material 3 is the default component library.

- Prefer native Angular Material components over custom implementations.
- Use Material components for buttons, inputs, forms, dialogs, menus, tables, tabs, tooltips, snackbars, and navigation.
- Use Material icons or the existing application icon system consistently.
- Follow Material 3 interaction patterns and component conventions.
- Use Material design tokens for colors, typography, shapes, and density.
- Do not recreate functionality already provided by Angular Material.
- Do not manipulate Angular Material internal DOM structures or private CSS classes.
- Avoid `::ng-deep` and arbitrary `!important` declarations.
- Customize components through supported theming APIs and documented customization points.

## 4. Design System & Design Tokens

A consistent design system is mandatory.

Never define arbitrary spacing, typography, colors, or component dimensions when an existing design token can be reused.

Establish centralized design tokens for:

- Spacing.
- Typography.
- Colors.
- Border radius.
- Elevation and shadows.
- Layout dimensions.
- Component density.
- Breakpoints.

### 4.1 Spacing System

Use a consistent 4px-based spacing scale.

Recommended spacing tokens:

| Token | Value | Usage |
|---|---:|---|
| `space-1` | 4px | Icon/text separation, micro spacing |
| `space-2` | 8px | Compact component spacing |
| `space-3` | 12px | Form field internal grouping |
| `space-4` | 16px | Standard component spacing |
| `space-5` | 20px | Related element grouping |
| `space-6` | 24px | Section internal spacing |
| `space-8` | 32px | Section separation |
| `space-10` | 40px | Major content separation |
| `space-12` | 48px | Page section separation |
| `space-16` | 64px | Large layout separation |

Rules:

- Prefer multiples of 4px.
- Use 8px as the default spacing unit.
- Use consistent spacing between elements of the same type.
- Related elements must have smaller spacing than unrelated groups.
- Separate major sections with visibly larger spacing.
- Avoid arbitrary margins and padding.
- Avoid excessive whitespace that reduces information density.
- Never use spacing inconsistently to compensate for incorrect component sizing.

Use CSS custom properties to centralize spacing tokens.

### 4.2 Spacing Hierarchy

Apply a consistent visual rhythm:

- Icon + label: 4–8px.
- Input label + input: 4–8px.
- Related form fields: 16–24px.
- Card internal padding: 16–24px.
- Card-to-card spacing: 16–24px.
- Section internal spacing: 24–32px.
- Page section separation: 32–48px.

These are starting guidelines, not rigid constraints. Adapt spacing according to component density, screen size, and content hierarchy.

Never apply the same spacing to every relationship between elements.

### 4.3 Layout and Alignment

- Use CSS Grid and Flexbox for layout composition.
- Establish consistent alignment between page titles, content sections, cards, and tables.
- Use a consistent page content container.
- Avoid arbitrary fixed widths.
- Prefer fluid layouts with sensible `max-width` constraints.
- Keep content visually balanced.
- Use `gap` instead of unnecessary individual margins when working with Flexbox and Grid.
- Avoid deeply nested containers without a clear layout purpose.
- Align form fields and actions consistently.
- Use consistent horizontal padding across related sections.

## 5. Typography System

Typography must establish a clear visual hierarchy and improve information comprehension.

Use Angular Material 3 typography tokens and typography configuration as the primary source of typography styles.

Do not assign arbitrary font sizes to individual elements.

### 5.1 Typography Hierarchy

Follow a consistent typographic scale:

| Role | Recommended size | Weight |
|---|---:|---:|
| Display | 36–48px | 600 |
| Page title | 28–32px | 600 |
| Section heading | 22–24px | 600 |
| Subsection heading | 18–20px | 500–600 |
| Body large | 16px | 400 |
| Body default | 14–16px | 400 |
| Supporting text | 12–14px | 400 |
| Overline / Label | 11–12px | 500 |

Use the closest appropriate Material 3 typography role instead of introducing custom levels unnecessarily.

### 5.2 Typography Rules

- Maintain a clear distinction between page titles, section headings, body text, labels, and metadata.
- Use font weights to reinforce hierarchy, not as decoration.
- Avoid excessive bold text.
- Avoid using multiple font families without a clear design reason.
- Prefer readable sans-serif fonts.
- Use consistent line heights.
- Body text should generally use a line height between 1.4 and 1.6.
- Headings should generally use a line height between 1.15 and 1.3.
- Use appropriate letter spacing.
- Avoid uppercase text for long headings or descriptions.
- Never use excessively small typography to fit more content into a screen.
- Maintain sufficient contrast between text and background.

### 5.3 Content Readability

- Avoid excessively long text lines.
- Prefer approximately 45–75 characters per line for reading-oriented content.
- Use paragraph spacing to distinguish separate ideas.
- Keep labels concise and descriptive.
- Use visual hierarchy to make important information scannable.
- Distinguish primary information from secondary metadata.
- Never communicate meaning exclusively through color.

## 6. Visual Hierarchy & UX Composition

Every screen must have an intentional information hierarchy.

Apply the following principles:

### Primary hierarchy
- Page title must be immediately identifiable.
- Main actions must be visually prominent.
- Important information must receive appropriate visual emphasis.
- Secondary actions must not compete with primary actions.

### Content grouping
- Group related information together.
- Use cards only when they represent meaningful content or interaction groups.
- Avoid unnecessary cards, borders, dividers, and containers.
- Prefer whitespace over excessive visual separators.
- Use consistent alignment and spacing within repeated components.

### Visual consistency
- Similar elements must look and behave consistently.
- Repeated patterns must use the same dimensions and spacing.
- Buttons with equivalent importance must have equivalent visual treatment.
- Forms must follow a consistent field layout.
- Tables must prioritize scanability and information density.
- Empty states must explain the situation and provide a useful next action.

### Avoid
- Excessive borders and shadows.
- Unnecessary gradients.
- Random border radii.
- Too many accent colors.
- Excessive use of badges.
- Overuse of cards.
- Inconsistent icon sizes.
- Decorative elements that compete with content.
- Artificially increasing visual complexity.

## 7. Visual Identity: Dark & Futuristic

Maintain a modern, dark, sophisticated and technology-oriented visual identity.

### Color system

- Use Material 3 surface hierarchy.
- Prefer semantic surface tokens such as `surface`, `surface-container-low`, `surface-container`, and `surface-container-high`.
- Use primary colors for important actions and selected states.
- Use secondary and tertiary colors sparingly.
- Reserve high-contrast accents for meaningful interactions.
- Avoid excessive neon colors and glow effects.
- Maintain sufficient contrast in all states.

### Surfaces and elevation

- Use surface variations to establish content hierarchy.
- Prefer subtle elevation differences over excessive shadows.
- Use borders only when they improve separation or comprehension.
- Keep card and dialog surfaces visually consistent.

### Interactive states

Define consistent visual states for:

- Default.
- Hover.
- Focus.
- Active.
- Selected.
- Disabled.
- Loading.
- Error.
- Success.

Never remove default Material focus indicators.

## 8. CSS & Styling Standards

- Use CSS exclusively for component styling.
- Never use inline `style` attributes.
- Never use `ngStyle`.
- Prefer class bindings over unnecessary `ngClass`.
- Use CSS custom properties for application-level design tokens.
- Keep component styles scoped and minimal.
- Avoid duplicated CSS declarations.
- Avoid unnecessary selectors and excessive specificity.
- Use semantic class names.
- Prefer reusable layout utilities for genuinely repeated patterns.
- Do not create a global utility framework for isolated use cases.

### Theming

- Consume Angular Material 3 CSS custom properties for component and application styling.
- Use supported Material theming APIs.
- When Sass theming is part of the project, use documented Angular Material Sass APIs such as `mat.theme` and `mat.theme-overrides` where appropriate.
- Do not assume undocumented Material CSS variables or internal component selectors.
- Avoid hardcoded HEX, RGB, or HSL colors in component stylesheets.
- Define application-specific semantic tokens centrally.

## 9. Responsive Design

Follow a mobile-first strategy.

- Design for small screens first.
- Use CSS media queries for responsive layout changes.
- Use Angular CDK `BreakpointObserver` only when application behavior or DOM composition must change dynamically.
- Avoid unnecessary TypeScript-based breakpoint detection for purely visual adjustments.
- Prefer fluid dimensions and CSS Grid/Flexbox.
- Avoid horizontal overflow.
- Ensure forms remain usable on mobile.
- Adapt navigation patterns to available screen space.
- Keep touch targets comfortably usable, following accessibility guidelines.
- Do not simply shrink desktop layouts to fit mobile screens.

## 10. Accessibility (WCAG)

Accessibility is a mandatory requirement.

- Use semantic HTML elements.
- Preserve Angular Material keyboard navigation.
- Maintain visible focus indicators.
- Provide accessible labels for form controls.
- Use appropriate ARIA attributes when necessary.
- Ensure sufficient color contrast.
- Do not rely exclusively on color to communicate status.
- Support keyboard-only navigation.
- Ensure dialogs and overlays follow accessible interaction patterns.
- Respect reduced-motion preferences.
- Use meaningful alternative text for informative images.
- Ensure interactive elements have accessible names.

## 11. UX Interaction Patterns

- Provide immediate feedback for user actions.
- Use loading indicators for asynchronous operations.
- Prevent accidental duplicate submissions.
- Provide clear validation messages.
- Display errors close to the relevant field or action.
- Preserve user input when validation fails.
- Confirm destructive actions when appropriate.
- Use snackbars for short-lived contextual feedback.
- Use dialogs only when an explicit decision or focused interaction is necessary.
- Avoid unnecessary confirmation dialogs.
- Provide useful empty, loading, success, and error states.

## 12. Performance & Maintainability

- Avoid unnecessary dependencies.
- Prefer native browser capabilities.
- Avoid excessive DOM nesting.
- Use lazy loading for feature areas when appropriate.
- Optimize images and other assets.
- Avoid unnecessary change detection and expensive template expressions.
- Keep components maintainable and reusable.
- Avoid abstractions that add complexity without practical benefits.

## 13. Mandatory UI Review Before Completion

Before considering any UI implementation complete, evaluate the interface against the following checklist.

### Visual consistency
- [ ] Is there a consistent spacing scale?
- [ ] Are elements properly aligned?
- [ ] Is the typography hierarchy clear?
- [ ] Are font sizes and weights consistent?
- [ ] Are margins and paddings intentional?
- [ ] Are colors based on design tokens?
- [ ] Is the visual identity consistent?

### UX quality
- [ ] Is the primary action immediately identifiable?
- [ ] Is information organized into meaningful groups?
- [ ] Is the interface easy to scan?
- [ ] Is unnecessary visual complexity avoided?
- [ ] Are loading, empty, success, and error states handled?

### Responsive behavior
- [ ] Does the layout work on mobile?
- [ ] Does it adapt correctly to tablet and desktop?
- [ ] Is horizontal overflow avoided?
- [ ] Are interactive elements usable on touch devices?

### Accessibility
- [ ] Are semantic elements used correctly?
- [ ] Are keyboard interactions preserved?
- [ ] Are focus indicators visible?
- [ ] Is text contrast sufficient?
- [ ] Are form controls accessible?

### Implementation quality
- [ ] Are Angular Material components preferred?
- [ ] Are modern Angular APIs used appropriately?
- [ ] Are CSS design tokens reused?
- [ ] Are unsupported Material overrides avoided?
- [ ] Is unnecessary CSS avoided?

## 14. Final Implementation Directive

Do not optimize only for functional correctness.

Every delivered interface must look intentional, consistent, polished, and production-ready.

When implementing or modifying a screen:

1. Understand the information hierarchy.
2. Establish the layout structure.
3. Apply the spacing system.
4. Apply the typography hierarchy.
5. Use Angular Material components and design tokens.
6. Validate responsiveness.
7. Validate accessibility.
8. Review visual consistency before completion.

When improving an existing interface, preserve its business logic and functional behavior unless explicitly requested otherwise.

Prioritize usability, readability, consistency, and visual quality over decorative complexity.