---
trigger: always_on
---

## Frontend Rule (Angular + Material)

- Frontend uses Angular
- Use Angular Material as the primary UI framework
- Prefer built-in Material components over custom HTML/CSS
- Follow Material Design guidelines (spacing, elevation, responsiveness)
- Always separate:
  - TypeScript → `.ts`
  - Template → `.html`
  - Styles → `.css`

## Styling Constraints

- Minimal custom CSS
- Use Angular Material theming (palette, typography, density)
- Prefer utility classes and layout APIs (Flex/Layout) over custom styles
- Avoid overriding Material styles unless strictly necessary
- No inline styles

## Responsiveness

- Use Angular Material grid / flex patterns
- Mobile-first approach
- Ensure components adapt to different breakpoints

## Visual Style

- Modern, dark, futuristic look
- Use theme configuration instead of hardcoded colors
- Subtle use of gradients and glow only when needed

## Avoid

- Heavy CSS files
- Custom components when Material equivalent exists
- Rewriting layout logic already handled by Material