# <img src="web/assets/logo.png" alt="NXGuard Logo" width="60" align="center"> NXGuard

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Version](https://img.shields.io/badge/Version-v1.0.6-green.svg)](https://github.com/liberatti/nxguard)
[![Platform](https://img.shields.io/badge/Platform-Docker-blue.svg)](https://www.docker.com/)

**NXGuard** is a high-performance, secure API Gateway and Reverse Proxy powered by **OpenResty** and **ModSecurity**. It
provides a robust layer of protection for your API ecosystem, ensuring scalability, security, and operational
simplicity.

---

## 🚀 Key Features

- **🛡️ Advanced Security:** Native integration with **ModSecurity v3** for real-time threat detection (SQLi, XSS, etc.).
- **⚡ High Performance:** Leverages the power of **OpenResty (Nginx + LuaJIT)** for sub-millisecond request processing.
- **📊 Real-time Monitoring:** Detailed transaction logging and telemetry for proactive threat identification.
- **⚖️ Smart Load Balancing:** Sophisticated traffic distribution across backend services.
- **🛠️ Operational Simplicity:** Lightweight architecture with a modern management interface.
- **🌐 Scalability:** Modular design built for horizontal scaling in containerized environments.

---

## 📸 Dashboard Preview

![NXGuard Dashboard Preview](web/assets/dashboard_mockup.png)
*Modern, intuitive management interface for full control over your API security.*

---

## 🏗️ Architecture

![NXGuard Architecture Diagram](web/assets/architecture_diagram.png)
*High-performance architecture integrating OpenResty, ModSecurity, and Redis.*

---

## 🚦 Getting Started

### Quick Start with Docker Compose

Deploy a full NXGuard stack including the Management UI and ipxa in seconds:

```yaml
services:
  redis:
    image: redis:7.2
    command: ["redis-server", "--save", "", "--appendonly", "no"]

  nxguard:
    image: liberatti/nxguard:latest
    environment:
      NXGUARD_ROLE: "main"
      SERVERID: "nxguard-admin"
    ports:
      - 5000:5000
      - 80:80
      - 443:443
    deploy:
      resources:
        limits:
          memory: 256M

  ipxa:
    image: liberatti/ipxa:latest
    volumes:
      - ipxa_data:/opt/ipxa/data
    deploy:
      resources:
        limits:
          memory: 64M
      replicas: 2

volumes:
  ipxa_data:
```

- **Management Interface:** [http://localhost:5000](http://localhost:5000)
- **Default Credentials:** `admin@nxguard.local` / `admin`

---

## 🧪 Security Validation

Validate your WAF rules using **GoTestWAF**:

```bash
docker run --rm -v ${PWD}/reports:/app/reports \
    wallarm/gotestwaf --url=https://<YOUR_ENDPOINT> --noEmailReport
```

---

## 🔢 WAF Rule ID Reservations

| Range                     | Description                |
|:--------------------------|:---------------------------|
| **1 - 99,999**            | Local/Internal Use         |
| **100,000 - 199,999**     | Oracle Published Rules     |
| **200,000 - 299,999**     | Comodo Published Rules     |
| **300,000 - 399,999**     | GotRoot.com Rules          |
| **900,000 - 999,999**     | OWASP Core Rule Set (CRS)  |
| **2,000,000 - 2,999,999** | Trustwave SpiderLabs Rules |

---

## 📡 Telemetry Notice

To improve our security engine, NXGuard collects anonymous traffic statistics over 24-hour cycles. **No sensitive,
personal, or request-specific data is ever collected.** This information is used solely to enhance threat detection
accuracy.

---

## 📄 License

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for the full text.

---
Developed with ❤️ by **Gustavo Liberatti**