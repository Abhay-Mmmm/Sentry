# Project: Sentinel

> **Company:** The Purple Movement
> **Vertical:** Cybersecurity / Developer Tools
> **Type:** Open Source
> **Status:** Completed (Sprint 1)

---

## Project Summary

Project Sentinel is an entirely offline, privacy-first system anomaly detection and explanation platform. It ingests simulated process-level telemetry (CPU, memory, network, disk I/O), applies an unsupervised machine learning model (Isolation Forest) to surface statistical outliers in real time, and feeds those anomalies to a locally hosted large language model (Gemma 4B) to generate human-readable security narratives — all without a single byte leaving the machine.

---

## Motivation

Modern endpoint monitoring solutions are cloud-dependent, privacy-invasive, or require significant infrastructure. Developers and security professionals need a lightweight, offline-capable tool that can detect anomalous process behavior and explain it in plain language without sending telemetry to external servers.

---

## Goals

- Detect process-level anomalies using unsupervised ML (Isolation Forest)
- Generate human-readable security analysis via local LLM (Gemma 4B via Ollama)
- Run entirely offline with zero external network calls
- Provide a simple Streamlit dashboard for visualization

---

## Technical Approach

**Architecture:** Monolithic Streamlit application with three functional domains:

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Streamlit | Dashboard, metrics, anomaly tables |
| ML Engine | scikit-learn Isolation Forest | Anomaly detection on process telemetry |
| LLM Bridge | Ollama + Gemma 4B | Security narrative generation |

**Data Flow:**
1. Synthetic process telemetry generated with NumPy (500 samples)
2. Isolation Forest model scores and flags anomalies (~5% contamination)
3. Top 5 anomalies + baseline snapshot sent to Gemma 4B
4. LLM returns security analysis displayed in dashboard

---

## Milestones

| Milestone | Description | Target Date |
|---|---|---|
| M1 | Environment setup, dependencies, model.pkl creation | Completed |
| M2 | Data generation + anomaly detection pipeline | Completed |
| M3 | LLM bridge integration with Gemma 4B | Completed |
| M4 | Streamlit dashboard with full pipeline | Completed |

---

## How to Contribute

**Skills Needed:**
- Python (pandas, numpy, scikit-learn)
- Streamlit for UI development
- Ollama/LLM integration
- Optional: eBPF, psutil for live telemetry

**Getting Started:**
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Pull Gemma model: `ollama pull gemma4:e4b`
4. Run the app: `streamlit run app.py`

---

## Current Contributors

| Name | GitHub | Role |
|---|---|---|
| Abhay | Abhay-Mmmm | Project Lead |
| Vander | Van-der | Team 3 - LLM Bridge |

---

## Related Problem Statements

- Local endpoint security monitoring without cloud dependency
- Explainable AI for anomaly detection

---

## Resources

- [Isolation Forest Paper](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf)
- [Ollama Documentation](https://ollama.com/docs)
- [Gemma Model Card](https://ollama.com/library/gemma)

---

*Part of Beyond Borders by The Purple Movement.*
