<img width="1024" height="1024" alt="WhatsApp Image 2026-04-14 at 23 23 16" src="https://github.com/user-attachments/assets/3651eac1-1dbf-4c04-a211-3b68db01ba6c" />


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Bitcoin Core](https://img.shields.io/badge/Bitcoin-Core%200.21+-orange.svg)](https://bitcoincore.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

> **Next‑gen Bitcoin instrumentation engine** — high‑speed wallet analytics, transaction monitoring, and automated trading execution with enterprise-grade security.

BBitcoin Pegasus combines the reliability of Bitcoin Core with a lightweight, async‑first architecture. Whether you are a trader, on-chain analyst, or infrastructure engineer, Pegasus gives you wings.

---

## ✨ Features

- 🚀 **Blazing‑fast RPC** – Async JSON‑RPC 2.0 client with connection pooling and automatic retries.
- 🧠 **Smart wallet scanner** – Real‑time UTXO aggregation, balance history, and label inference.
- 📡 **Zero‑MQ subscriber** – Low‑latency mempool and block notifications.
- 🤖 **Rule engine** – Define custom triggers (e.g., "alert when large tx > 10 BTC enters mempool").
- 🔒 **Hardened security** – Encrypted config, optional HSM integration, and automatic rate limiting.
- 📊 **Prometheus metrics** – Export all key performance indicators for Grafana dashboards.
- 🐳 **One‑line Docker** – Fully containerized deployment with `docker-compose up`.

---

## 📦 Installation

### Prerequisites
- Bitcoin Core 0.21+ (with `txindex=1` and ZMQ enabled)
- Python 3.9+ or Docker 20.10+

### From Source
```bash
git clone https://github.com/your-org/bbitcoin-pegasus.git
cd bbitcoin-pegasus
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your RPC credentials
