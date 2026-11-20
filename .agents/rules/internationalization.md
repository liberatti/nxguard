---
trigger: always_on
---

# Internationalization

- The frontend uses `@ngx-translate/core`. Translation files are in
  `web/assets/i18n/{lang}.json`; keep `en_US.json` and `pt_BR.json` strictly synchronized
  and up to date with tags used and removed in code.
- Prune obsolete or unused translation keys immediately whenever templates, components,
  or features are modified or deleted; never leave orphaned tags in translation files.
- Put all user-visible text, including labels, placeholders, accessibility text, and
  UI error messages, in translation files. Do not display raw backend error strings.
- Use hierarchical `SCREAMING_SNAKE_CASE` keys, such as
  `AUTH.LOGIN.SUBMIT_BUTTON`, and follow the existing key conventions where they
  differ.
- Use the `translate` directive for static template text and the pipe for
  interpolated values or attributes. Prefer reactive translation APIs such as
  `stream()` when language changes must be reflected; avoid `instant()` before the
  translations have loaded.
- Use Angular's date, number, and currency pipes for formatting, with the
  application's locale configuration. Do not use translation keys to format values.
- Avoid concatenating translated fragments or implementing pluralization with manual
  conditionals. Use complete messages and interpolation supported by the project.
- Return stable error codes from the API when the UI needs to display localized
  errors, and map those codes to translations in the frontend.
