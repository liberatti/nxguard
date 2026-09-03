---
trigger: always_on
---

# Skill: minimal_code_editor

## Objective
Execute surgical, deterministic, and review-friendly edits on Python codebases.  
Output only raw code or standard unified diffs designed for immediate manual review.

---

## Output Protocol (Zero-Fluff)

- **Default Format:** Standard `unified diff` with standard 2–3 lines of anchoring context.
- **Full File Exception:** Return full file inside a single fenced code block (` ```python `) ONLY for new files or files under 40 lines.
- **Text Rules:**
  - Zero conversational filler, greetings, or sign-offs.
  - Zero explanations, rationales, or justifications.
  - No markdown text, titles, or headers outside the code fence.
  - At most: a single line of critical technical context preceding the block if, and only if, a breaking dependency or migration step is required.

---

## Python Engineering Standards

- **Formatting & Linting:** Strict adherence to PEP 8 and **Ruff/Flake8** defaults:
  - Line length: maximum 88 characters.
  - Proper import sorting (standard lib -> third-party -> local).
  - Zero unused imports or variables.
  - Zero trailing whitespace; ensure terminal newline.
- **Type Annotations:**
  - Use modern built-in generics (`list[str]`, `dict[str, Any]`, `X | None`) over deprecated `typing` constructs where possible.
- **Docstrings:** Match existing project conventions. If creating new modules, default strictly to NumPy style.

---

## Surgical Modification Rules

- **Scope Boundary:** Modify exclusively the logic requested. Never reformat, reorder, or rename unrelated code.
- **Dependency Guard:** Do not introduce third-party dependencies unless explicitly requested.
- **No Artifacts:** Never leave debug statements (`print`, breakpoint), ad-hoc logging, or extraneous comments.

---

## Pre-Response Verification Checklist

Before emitting the block, verify internally:
1. Syntax is 100% valid Python.
2. Diff headers (`---`, `+++`, `@@`) and line anchors are syntactically accurate.
3. All imports used in modified blocks are properly declared.
4. No explanatory prose exists outside the code fence.