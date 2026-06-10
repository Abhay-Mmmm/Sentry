# Project Sentinel — Summary

## What It Does

Project Sentinel monitors your machine's running processes in real time, flags statistically unusual behaviour using an Isolation Forest model trained on your own system's baseline, and generates a plain-English security analysis using a locally hosted Gemma 4B LLM. Everything runs offline.

---

## Pipeline

```
collect_data.py  →  data/live_data.json  →  ml_pipeline.py  →  model.pkl
                                                                    │
                                                              api.py (FastAPI)
                                                                    │
                                                     ┌──────────────┴──────────────┐
                                                     │                             │
                                              /api/snapshot                   /api/llm
                                             (live psutil +               (Gemma 4B via
                                              IsoForest scoring)              Ollama)
                                                     │
                                              frontend/ (React SPA)
                                             client-side whitelist overlay
```

---

## Key Files

| File | Purpose |
|------|---------|
| `collect_data.py` | Runs once. Captures 120s of psutil telemetry at 1s intervals → `data/live_data.json` |
| `ml_pipeline.py` | Trains `IsolationForest` on `live_data.json` → `model.pkl` |
| `api.py` | FastAPI server — snapshot, whitelist, and LLM endpoints |
| `app.py` | Streamlit fallback — works independently without the React frontend |
| `frontend/` | React + Vite + TypeScript SPA — the primary UI |
| `whitelist.json` | Persists user-approved process exemptions across sessions |

---

## Dashboard Sections

| Section | Description |
|---------|-------------|
| Metric cards | Total processes, anomalies detected, anomaly rate %, whitelisted count |
| Process Health doughnut | Normal / Anomaly / Whitelisted breakdown — hover for count + % |
| Top CPU bar chart | Top 10 processes by CPU, coloured by anomaly status |
| CPU vs Memory scatter | All processes plotted; hover for per-process detail |
| Flagged Anomalies tab | Checkbox-select anomalies → "Ignore Selected" to whitelist instantly |
| All Processes tab | Full sortable telemetry table (click any column header to sort) |
| Whitelist tab | Manage whitelisted names — remove to immediately restore to Flagged Anomalies |
| LLM Analysis | On-demand Gemma 4B security narrative for top 5 non-whitelisted anomalies |

---

## Status Colours

| Colour | Meaning |
|--------|---------|
| 🟢 Green | Normal process |
| 🔴 Red | Active anomaly — investigate |
| 🟡 Yellow | Whitelisted — previously flagged, user-approved as safe |

---

## Run Commands

```bash
# First-time setup
python collect_data.py      # ~2 minutes
python ml_pipeline.py

# React UI (recommended)
python api.py               # Terminal 1 — API on :8000
cd frontend && npm run dev  # Terminal 2 — UI on :5173

# Streamlit fallback
streamlit run app.py

# Production (built SPA served by FastAPI)
cd frontend && npm run build && cd .. && python api.py
```

---

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/snapshot` | GET | Live 1s psutil snapshot scored by model |
| `/api/whitelist` | GET | Current whitelist names |
| `/api/whitelist/add` | POST | Add names `{ "names": [...] }` |
| `/api/whitelist/remove` | POST | Remove name `{ "name": "..." }` |
| `/api/llm` | POST | Gemma 4B analysis of current anomalies |

---

## LLM Bridge

- **Model:** `gemma4:e4b` via Ollama at `localhost:11434`
- **Input:** Top 5 anomalies by score (whitelisted names excluded) + system baseline summary
- **Output:** 3–5 sentence threat classification with investigation recommendation
- **Timeout:** 120 seconds
- **Fallback:** Returns descriptive error string if Ollama is unreachable — never crashes the app
