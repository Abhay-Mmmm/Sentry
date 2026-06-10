# Project Sentinel

> **Company:** The Purple Movement
> **Vertical:** Cybersecurity / Developer Tools
> **Type:** Open Source
> **Status:** Active — Sprint 3 Complete

---

## Summary

Project Sentinel is an entirely offline, privacy-first endpoint anomaly detection platform. It captures live process telemetry from the host machine using `psutil`, trains an Isolation Forest model on that real-world baseline, and scores a fresh snapshot every time the dashboard is opened. Anomalies are explained in plain English by a locally hosted Gemma 4B LLM via Ollama — no data ever leaves the machine.

---

## Motivation

Modern endpoint monitoring solutions are cloud-dependent, privacy-invasive, or require significant infrastructure. Developers and security professionals need a lightweight, offline-capable tool that detects anomalous process behaviour and explains it in plain language, trained on their own system's normal baseline rather than generic synthetic data.

---

## Goals

- Capture real live process telemetry using `psutil` (not synthetic data)
- Train an Isolation Forest on the actual system's process baseline
- Detect anomalies on a fresh live snapshot at every app launch
- Allow users to whitelist known-safe processes that recur as false positives
- Generate human-readable security analysis via a local LLM (Gemma 4B)
- Run entirely offline with zero external network calls
- Serve a premium React UI via FastAPI with the Streamlit version kept as a fallback

---

## Architecture

| Component | File | Technology | Purpose |
|-----------|------|------------|---------|
| Data Collector | `collect_data.py` | psutil | 2-min live telemetry capture at 1s intervals |
| ML Pipeline | `ml_pipeline.py` | scikit-learn IsolationForest | Train + save model on real baseline |
| API Server | `api.py` | FastAPI + uvicorn | REST API serving snapshot, whitelist, LLM endpoints |
| React UI | `frontend/` | Vite + React + TypeScript + Tailwind | Primary dashboard SPA |
| Streamlit UI | `app.py` | Streamlit + Plotly | Fallback dashboard (runs independently) |
| LLM Bridge | `api.py` / `app.py` | Ollama + Gemma 4B | Natural language security analysis |
| Whitelist | `whitelist.json` | JSON | Persistent user-granted process exemptions |

---

## Data Flow

1. **`collect_data.py`** runs once — captures 120 snapshots of all running processes at 1-second intervals, computing per-second deltas for network and disk I/O. Saves to `data/live_data.json`.
2. **`ml_pipeline.py`** trains `IsolationForest(n_estimators=200, contamination=0.05)` on the collected data and saves `model.pkl`.
3. On each request to `/api/snapshot`, **`api.py`** takes a fresh 1-second live psutil snapshot, scores it against `model.pkl`, and returns `"anomaly"` or `"normal"` for each process.
4. The React frontend applies the whitelist overlay client-side — whitelist add/remove is instant without a re-fetch.
5. The top 5 anomalies (excluding whitelisted names) are sent to Gemma 4B for threat analysis via `/api/llm`.

---

## Feature Columns

The model trains and scores on 4 features:

| Feature | Source | Notes |
|---------|--------|-------|
| `cpu_percent` | psutil | Per-process CPU over 1s interval |
| `memory_mb` | psutil RSS | Resident set size in MB |
| `net_bytes_sent` | psutil net_io_counters | System-wide delta apportioned per process |
| `disk_read_ops` | psutil io_counters | Per-process read count delta over 1s |

---

## Whitelist System

The whitelist is managed client-side for instant reactivity:

- **Flagged Anomalies** tab shows checkboxes for each anomalous process
- Selecting any and clicking **"Ignore Selected"** optimistically updates the local state immediately and then persists to `whitelist.json` via `/api/whitelist/add`
- Whitelisted processes instantly disappear from Flagged Anomalies and appear in the Whitelist tab
- Removing from the Whitelist tab restores the process to Flagged Anomalies immediately
- Whitelist persists across restarts via `whitelist.json`

---

## Milestones

| Milestone | Description | Status |
|-----------|-------------|--------|
| M1 | Environment setup, venv, dependencies | ✅ Done |
| M2 | Live data collection via psutil (`collect_data.py`) | ✅ Done |
| M3 | Real-data ML pipeline — train + save `model.pkl` | ✅ Done |
| M4 | Live snapshot inference | ✅ Done |
| M5 | LLM bridge with Gemma 4B via Ollama | ✅ Done |
| M6 | Streamlit dashboard with Plotly charts | ✅ Done |
| M7 | Whitelist system with persistent `whitelist.json` | ✅ Done |
| M8 | FastAPI backend replacing Streamlit as primary UI server | ✅ Done |
| M9 | React + TypeScript SPA (Vite + Tailwind) with real-time whitelist overlay | ✅ Done |

---

## Setup & Usage

```bash
# 1. Create venv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Pull the LLM model
ollama pull gemma4:e4b

# 3. Collect 2 minutes of baseline telemetry
python collect_data.py

# 4. Train the model
python ml_pipeline.py

# 5a. Run the React UI (recommended)
python api.py &                      # API on :8000
cd frontend && npm run dev           # UI on :5173

# 5b. Run the Streamlit fallback
streamlit run app.py
```

> Re-run steps 3 and 4 any time you want to retrain the baseline.

---

## Project Structure

```
Sentry/
├── api.py              # FastAPI server — /api/snapshot, /api/whitelist, /api/llm
├── app.py              # Streamlit fallback (kept for compatibility)
├── collect_data.py     # psutil 2-min telemetry collector
├── ml_pipeline.py      # IsolationForest training on live_data.json
├── model.pkl           # Trained model (generated)
├── whitelist.json      # User-granted process exemptions (auto-created)
├── requirements.txt
├── data/
│   └── live_data.json  # Raw telemetry from collect_data.py
└── frontend/           # React + Vite + TypeScript SPA
    ├── src/
    │   ├── App.tsx
    │   ├── components/sentinel/
    │   ├── hooks/useSentinelStore.ts
    │   └── lib/api.ts
    ├── package.json
    └── vite.config.ts
```

---

## Contributors

| Name | GitHub | Role |
|------|--------|------|
| Abhay | Abhay-Mmmm | Project Lead |
| Vander | Van-der | LLM Bridge + Dashboard + React UI |

---

## Resources

- [Isolation Forest Paper](https://cs.nju.edu.cn/zhouzh/zhouzh.files/publication/icdm08b.pdf)
- [Ollama Documentation](https://ollama.com/docs)
- [Gemma Model Card](https://ollama.com/library/gemma)
- [psutil Documentation](https://psutil.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

*Part of Beyond Borders by The Purple Movement.*
