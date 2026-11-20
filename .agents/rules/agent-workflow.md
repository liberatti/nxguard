---
trigger: always_on
---

# Agent workflow and change discipline

- Read the files directly related to the task and inspect nearby code before editing.
  Follow references only as far as needed to preserve behavior and contracts.
- Preserve existing user changes. Do not revert unrelated work or overwrite local
  edits while solving another task.
- Keep changes focused. Avoid unrelated refactors, reformatting, new dependencies,
  generated files, or configuration changes.
- Follow repository conventions and update directly related documentation when
  behavior or workflows change.
- Run the smallest relevant build, test, or validation command. Report what ran and
  disclose checks that could not be performed; never imply an unrun check passed.
- Surface errors explicitly. Do not hide failures behind broad exception handling,
  silent defaults, or success-shaped fallbacks.
- Do not deploy, publish artifacts, modify shared environments, or perform
  destructive actions without explicit authorization.
