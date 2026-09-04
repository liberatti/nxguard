---
trigger: always_on
---

# Agent Execution Rules: Context, Diffs & Precision

## Context Boundary & Token Economy

- **Targeted Scope:** Read and modify only files directly relevant to the user's task.
- **Reference Awareness:** Inspect external symbols, imports, or type signatures only when strictly necessary to ensure zero build breaks.
- **No Unsolicited Scans:** Do not recursively scan unrelated project directories or re-read unchanged files.

---

## Diff Minimization & Patch Integrity

- **Surgical Edits:** Modify only the exact lines required to satisfy the prompt. Never reformat, reorder, or restyle untouched code.
- **Valid Context Anchors:** Include minimal surrounding context (2–3 lines) around edits to guarantee unique and reliable patch anchoring.
- **Single-Hunk Preference:** Group adjacent modifications into a single unified hunk instead of multiple fragmented edits.

---

## Deterministic Execution

- **Zero Scope Creep:** Execute strictly what was requested. Do not implement unprompted refactorings, optimizations, or architectural changes.
- **Single Direct Solution:** Provide one implementation matching the codebase conventions; do not present multiple alternative approaches.
- **No Fluff or Tangents:** Omit generic conversational filler, promotional commentary, or unsolicited architectural suggestions.
- **Critical Safety Exception:** If the requested change introduces a severe breaking change, syntax error, or direct security vulnerability, state it in a single concise sentence before the code.