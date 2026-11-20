# Security Policy

## 🛡️ Supported Versions

We provide patches and security fixes for the currently supported versions of NXGuard.

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < 1.0   | :x:                |

---

## 🚨 Reporting a Vulnerability

The NXGuard team takes security reports seriously and appreciates responsible disclosure.

### Private Reporting (Recommended)

Please **do not** report security vulnerabilities through public issues or pull requests.

Instead, use one of the following private reporting methods:

1. **GitHub Security Advisory:** Submit a report through [GitHub Private Vulnerability Reporting](https://github.com/liberatti/nxguard/security/advisories/new).
2. **Email:** If private reporting is unavailable, email the maintainer at [gustavo@liberatti.net](mailto:gustavo@liberatti.net) with the details.

### What to Include in Your Report

To help us investigate and reproduce the issue, include:

- A clear description of the vulnerability and its potential impact.
- Step-by-step reproduction instructions or a proof of concept (PoC).
- The affected component (for example, the OpenResty engine, ModSecurity rules, Management API, or web UI).
- Relevant environment details, such as the operating system, Docker version, and deployment configuration.
- Any proposed remediation or mitigation steps, if available.

### Response & Disclosure Process

- **Acknowledgment:** We aim to acknowledge your report within 48 hours.
- **Assessment & Triage:** We will validate the report and assess the vulnerability's severity.
- **Fix & Testing:** We will develop and verify a security patch.
- **Public Disclosure:** Once a fix is ready, we will publish a release containing the patch along with a security advisory.

---

## 🔒 Security Best Practices for NXGuard Deployments

When deploying NXGuard in production, follow these recommendations:

1. **Default Credentials:** Change the default administrator credentials (`admin@nxguard.local` / `admin`) immediately after deployment.
2. **Secret Management:** Never commit sensitive configuration files, API tokens, or session secrets to version control. Store them in environment variables or a secrets manager.
3. **TLS Encryption:** Require HTTPS (TLS 1.2 or later) for all externally accessible endpoints and management interfaces.
4. **WAF Rule Maintenance:** Keep the ModSecurity engine and OWASP Core Rule Set (CRS) up to date to address newly emerging threats.
5. **Network Isolation:** Restrict access to internal ports and administrative interfaces to trusted networks or internal VPCs.
