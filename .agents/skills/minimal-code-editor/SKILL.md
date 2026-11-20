---
name: minimal-code-editor
description: Use when making focused Python changes that should produce a small, reviewable diff with no unrelated edits.
---

# Minimal Python editor

Make the smallest change that fully addresses the request. Match nearby code and
return a standard unified diff. For a new file or a file under 40 lines, return the
complete file in a Python code block. Do not add conversational filler or unrelated
explanations.

## Python conventions

- Follow the repository's formatting and import conventions. Use an 88-character
  line limit when no local formatter configuration takes precedence.
- Group standard-library, third-party, and local imports. Keep imports at module
  scope; do not import inside functions, methods, loops, or conditionals.
- Avoid unused imports and variables, trailing whitespace, and missing final
  newlines.
- Prefer built-in generics and modern union syntax when compatible with the project's
  supported Python version.
- Match existing docstring conventions. For new modules, use NumPy-style docstrings
  only when the project has no established convention.

## Change boundaries

- Do not reformat, rename, or refactor unrelated code.
- Do not introduce dependencies unless the task requires them.
- Do not leave debug output, breakpoints, or temporary comments.
- When moving a module, update its consumers rather than adding a re-export shim.

## Review

Check syntax, imports, and diff scope. Run the smallest relevant validation available
and report checks that could not be performed.
