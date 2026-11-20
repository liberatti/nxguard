---
trigger: always_on
---

# Secure development

NXGuard is a security gateway. Apply these safeguards to new and modified code:

- Never commit credentials, tokens, private keys, certificates, or personal data.
  Use the project's configuration mechanisms and identify secrets that operators
  must provide.
- Validate inputs at application boundaries. Preserve authentication, authorization,
  certificate validation, size limits, and existing security controls.
- Do not weaken CORS, TLS, JWT, or WAF controls to make tests pass.
- Do not expose stack traces, secrets, or sensitive request data in responses or logs.
  When touching existing flows, do not expand exposure; keep errors consistent with
  the API contract.
- Mask sensitive headers in audit logs. Avoid recording request bodies unless the
  feature requires it and appropriate protection is in place.
- Treat changes to ModSecurity rules, authentication, certificates, and exposed ports
  as high impact. Explain material behavior changes and validate locally before
  recommending operational use.
- Keep dependency manifests and lockfiles consistent. Prefer supported versions and
  add dependencies only when justified.

Do not make unrelated security refactors without authorization.
