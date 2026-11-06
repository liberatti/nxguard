# Security Policy

## 🛡️ Supported Versions

We release patches and security fixes for currently supported versions of NXGuard.

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < 1.0   | :x:                |

---

## 🚨 Reporting a Vulnerability

The NXGuard team takes security vulnerabilities seriously. We appreciate your efforts to responsibly disclose any findings.

### Private Reporting (Recommended)

Please **do not** open public issues or pull requests for security vulnerabilities.

Instead, please report security issues through one of the following methods:

1. **GitHub Security Advisory:** Submit a report via [GitHub Private Vulnerability Reporting](https://github.com/liberatti/nxguard/security/advisories/new).
2. **Email Disclosure:** If private reporting is unavailable, reach out directly to the maintainer at [gustavo@liberatti.net](mailto:gustavo@liberatti.net) with details.

### What to Include in Your Report

To help us investigate and reproduce the issue quickly, please include:
- A clear description of the vulnerability and its potential impact.
- Step-by-step instructions or Proof of Concept (PoC) to reproduce the issue.
- The affected component (e.g., OpenResty engine, ModSecurity rules, Management API, Web UI).
- Relevant environment details (OS, Docker version, deployment configuration).
- Any proposed remediation or mitigation steps, if available.

### Response & Disclosure Process

- **Acknowledgment:** We will acknowledge receipt of your report within 48 hours.
- **Assessment & Triage:** We will validate and determine the severity of the vulnerability.
- **Fix & Testing:** We will develop and verify a security patch.
- **Public Disclosure:** A new release containing the patch and a security advisory will be published coordinately.

---

## 🔒 Security Best Practices for NXGuard Deployments

When deploying NXGuard in production environments, ensure you follow these recommendations:

1. **Default Credentials:** Immediately change the default admin credentials (`admin@nxguard.local` / `admin`) after initial deployment.
2. **Secret Management:** Never commit sensitive configuration files, API tokens, or session secrets to version control. Use environment variables or secret managers.
3. **TLS/SSL Encryption:** Ensure HTTPS (TLS 1.2+) is enforced on all external-facing endpoints and management interfaces.
4. **WAF Rule Maintenance:** Keep the ModSecurity engine and OWASP Core Rule Set (CRS) updated to protect against newly emerging threat vectors.
5. **Network Isolation:** Restrict access to internal ports and administrative interfaces to trusted networks or internal VPCs.
