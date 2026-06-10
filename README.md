# Project Sentinel — Local System Anomaly Monitor

> **Entirely offline. Zero cloud. Privacy-first.**

A local-only endpoint security monitor that detects statistically anomalous process behaviour using an Isolation Forest model trained on your own system's baseline, then explains the findings in plain English using a locally hosted Gemma 4B LLM via Ollama.

---

## Architecture

```
collect_data.py  →  data/live_data.json  →  ml_pipeline.py  →  model.pkl
                                                                    │
                                               ┌────────────────────┤
                                               │                    │
                                          api.py (FastAPI)    app.py (Streamlit fallback)
                                               │
                                       frontend/ (React SPA)
                                               │
                                    localhost:5173 (dev)
                                    localhost:8000 (prod)
```

---

## Quick Start

### 1. Install Python dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Pull the LLM model

```bash
# Install Ollama first: https://ollama.com/download
ollama pull gemma4:e4b
```

### 3. Collect baseline telemetry (~2 minutes)

```bash
python collect_data.py
```

### 4. Train the model

```bash
python ml_pipeline.py
```

### 5. Run the app

**Option A — React UI (recommended):**

```bash
# Terminal 1: start the API server
python api.py                    # → http://localhost:8000

# Terminal 2: start the dev server (hot reload)
cd frontend && npm install && npm run dev   # → http://localhost:5173
```

**Option B — Streamlit fallback:**

```bash
streamlit run app.py             # → http://localhost:8501
```

**Production (single server — React SPA served by FastAPI):**

```bash
cd frontend && npm run build
cd .. && python api.py           # → http://localhost:8000 serves UI + API
```

---

## Project Structure

```
Sentry/
├── api.py              # FastAPI backend — snapshot, whitelist, LLM endpoints
├── app.py              # Streamlit fallback UI (keeps working independently)
├── collect_data.py     # One-time psutil telemetry collector (~2 min)
├── ml_pipeline.py      # Trains IsolationForest on live_data.json → model.pkl
├── model.pkl           # Trained model (generated — not committed)
├── whitelist.json      # User-granted process exemptions (auto-created)
├── requirements.txt    # Python dependencies
├── data/
│   └── live_data.json  # Raw baseline telemetry from collect_data.py
└── frontend/           # React + Vite + TypeScript SPA
    ├── src/
    │   ├── App.tsx
    │   ├── components/sentinel/   # Header, charts, tables, LLM panel
    │   ├── hooks/useSentinelStore.ts
    │   └── lib/api.ts             # Typed fetch client → /api/*
    ├── package.json
    └── vite.config.ts
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/snapshot` | Take a live 1s psutil snapshot, score with model |
| `GET` | `/api/whitelist` | Get current whitelist |
| `POST` | `/api/whitelist/add` | Add process names to whitelist |
| `POST` | `/api/whitelist/remove` | Remove a process name from whitelist |
| `POST` | `/api/llm` | Run Gemma 4B analysis on current snapshot anomalies |

---

## Retraining the Model

Run steps 3 and 4 again any time you want to rebuild the baseline — e.g. after installing new software or changing your typical workload:

```bash
python collect_data.py   # captures ~2 min of live telemetry
python ml_pipeline.py    # retrains and overwrites model.pkl
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `503` from `/api/snapshot` | Run `python ml_pipeline.py` first to generate `model.pkl` |
| LLM button returns "Ollama unreachable" | Run `ollama serve` in a separate terminal |
| `model not found` in LLM response | Run `ollama pull gemma4:e4b` |
| Blank dashboard on first load | API still taking the 1s snapshot — wait a moment |

---

## Status Colours

| Colour | Meaning |
|--------|---------|
| 🟢 Green | Normal process |
| 🔴 Red | Active anomaly — investigate |
| 🟡 Yellow | Whitelisted — user-approved false positive |

---

## License

MIT — *Part of Beyond Borders by The Purple Movement.*
