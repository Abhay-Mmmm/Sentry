# api.py — Project Sentinel · FastAPI backend for the React UI
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Optional

import joblib
import pandas as pd
import psutil
import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

OLLAMA_URL      = "http://localhost:11434/api/generate"
OLLAMA_MODEL    = "gemma4:e4b"
FEATURE_COLUMNS = ["cpu_percent", "memory_mb", "net_bytes_sent", "disk_read_ops"]
TOP_N_ANOMALIES = 5
MODEL_PATH      = "model.pkl"
WHITELIST_PATH  = "whitelist.json"
FRONTEND_DIST   = os.path.join(os.path.dirname(__file__), "frontend", "dist")

app = FastAPI(title="Project Sentinel API", version="1.0.0")

# Allow dev server to hit the API on a different port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_whitelist() -> set:
    if os.path.exists(WHITELIST_PATH):
        with open(WHITELIST_PATH) as f:
            return set(json.load(f))
    return set()


def save_whitelist(wl: set) -> None:
    with open(WHITELIST_PATH, "w") as f:
        json.dump(sorted(wl), f, indent=2)


def get_live_snapshot() -> pd.DataFrame:
    procs_before, net_before = {}, psutil.net_io_counters()
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info",
                                   "num_threads", "create_time", "status"]):
        try:
            io = p.io_counters()
            procs_before[p.pid] = {
                "proc": p,
                "io_read": io.read_count,
                "io_write": io.write_count,
                "conns": len(p.net_connections()),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    time.sleep(1)
    net_after = psutil.net_io_counters()
    n = len(procs_before) or 1
    net_sent = max(0, net_after.bytes_sent - net_before.bytes_sent) / n
    net_recv = max(0, net_after.bytes_recv - net_before.bytes_recv) / n
    ts = datetime.now(timezone.utc).isoformat()
    records = []
    for pid, prev in procs_before.items():
        p = prev["proc"]
        try:
            info = p.as_dict(attrs=["name", "cpu_percent", "memory_info",
                                     "num_threads", "create_time", "status"])
            if info["status"] in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):
                continue
            io = p.io_counters()
            records.append({
                "timestamp": ts,
                "process_name": info["name"],
                "pid": pid,
                "cpu_percent": round(info["cpu_percent"], 2),
                "memory_mb": round(info["memory_info"].rss / (1024 * 1024), 2),
                "thread_count": info["num_threads"],
                "net_bytes_sent": round(net_sent, 2),
                "net_bytes_recv": round(net_recv, 2),
                "open_connections": prev["conns"],
                "disk_read_ops": max(0, io.read_count - prev["io_read"]),
                "disk_write_ops": max(0, io.write_count - prev["io_write"]),
                "process_age_seconds": int(time.time() - info["create_time"]),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            pass
    return pd.DataFrame(records)


def run_anomaly_detection(df: pd.DataFrame, model):
    """Tag each process as 'anomaly' or 'normal' based purely on the model.
    Whitelist overlay is applied client-side so the frontend can react instantly.
    """
    df = df.copy()
    df["anomaly_score"] = model.score_samples(df[FEATURE_COLUMNS].values)
    df["is_anomaly"]    = model.predict(df[FEATURE_COLUMNS].values) == -1

    # Normalise score to [0, 1] range (IsoForest scores are negative;
    # more negative = more anomalous → we invert + scale for UI clarity)
    raw_scores = df["anomaly_score"].values
    min_s, max_s = raw_scores.min(), raw_scores.max()
    if max_s != min_s:
        df["anomaly_score_norm"] = 1.0 - (raw_scores - min_s) / (max_s - min_s)
    else:
        df["anomaly_score_norm"] = 0.0

    df["status"] = df["is_anomaly"].map({True: "anomaly", False: "normal"})
    return df


def get_llm_explanation(df_anomalies: pd.DataFrame, df_all: pd.DataFrame) -> str:
    try:
        top = df_anomalies.nsmallest(TOP_N_ANOMALIES, "anomaly_score")
        lines = [
            f"- {r['process_name']} (PID {r['pid']}) | CPU {r['cpu_percent']:.1f}% | "
            f"Mem {r['memory_mb']:.0f}MB | Net {r['net_bytes_sent']:.0f}B/s | "
            f"Disk {r['disk_read_ops']:.0f}r/s | Score {r['anomaly_score']:.4f}"
            for _, r in top.iterrows()
        ]
        prompt = f"""You are a cybersecurity analyst reviewing live system anomalies from an Isolation Forest model.

Baseline — {len(df_all)} processes | Avg CPU {df_all['cpu_percent'].mean():.1f}% | Avg Mem {df_all['memory_mb'].mean():.0f}MB

Flagged:
{chr(10).join(lines)}

Give a concise 3-5 sentence analysis: identify the threat class, explain why the values are suspicious, and recommend one immediate action. Be direct."""
        r = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, timeout=120)
        r.raise_for_status()
        return r.json().get("response", "Error: empty response.")
    except requests.exceptions.ConnectionError:
        return "Error: Ollama unreachable. Run `ollama serve`."
    except requests.exceptions.Timeout:
        return "Error: Timed out after 120s."
    except Exception as e:
        return f"Error: {e}"


# ── Load model once at startup ─────────────────────────────────────────────────

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            _model = joblib.load(MODEL_PATH)
        except FileNotFoundError:
            raise HTTPException(status_code=503, detail=f"'{MODEL_PATH}' not found. Run `python ml_pipeline.py` first.")
    return _model


# ── Pydantic models ────────────────────────────────────────────────────────────

class ProcessRow(BaseModel):
    process_name: str
    pid: int
    cpu_percent: float
    memory_mb: float
    net_bytes_sent: float
    disk_read_ops: int
    anomaly_score: float   # normalised 0–1 (1 = most anomalous)
    status: str            # "normal" | "anomaly" | "whitelisted"

class SnapshotResponse(BaseModel):
    generated_at: int      # epoch ms
    processes: list[ProcessRow]

class WhitelistRequest(BaseModel):
    names: list[str]

class RemoveRequest(BaseModel):
    name: str

class LlmResponse(BaseModel):
    report: str


# ── API routes ─────────────────────────────────────────────────────────────────

@app.get("/api/snapshot", response_model=SnapshotResponse)
def snapshot():
    """Take a live 1-second process snapshot and return annotated rows."""
    model = get_model()
    df_raw = get_live_snapshot()
    if df_raw.empty:
        return SnapshotResponse(generated_at=int(time.time() * 1000), processes=[])
    df = run_anomaly_detection(df_raw, model)
    processes = []
    for _, row in df.iterrows():
        processes.append(ProcessRow(
            process_name=row["process_name"],
            pid=int(row["pid"]),
            cpu_percent=float(row["cpu_percent"]),
            memory_mb=float(row["memory_mb"]),
            net_bytes_sent=float(row["net_bytes_sent"]),
            disk_read_ops=int(row["disk_read_ops"]),
            anomaly_score=round(float(row["anomaly_score_norm"]), 3),
            status=row["status"],
        ))
    return SnapshotResponse(
        generated_at=int(time.time() * 1000),
        processes=processes,
    )


@app.get("/api/whitelist")
def get_whitelist():
    return {"names": sorted(load_whitelist())}


@app.post("/api/whitelist/add")
def add_to_whitelist(req: WhitelistRequest):
    wl = load_whitelist()
    wl.update(req.names)
    save_whitelist(wl)
    return {"names": sorted(wl)}


@app.post("/api/whitelist/remove")
def remove_from_whitelist(req: RemoveRequest):
    wl = load_whitelist()
    wl.discard(req.name)
    save_whitelist(wl)
    return {"names": sorted(wl)}


@app.post("/api/llm", response_model=LlmResponse)
def llm_analysis():
    """Run LLM threat analysis on the current snapshot (takes ~30-120 s)."""
    model = get_model()
    whitelist = load_whitelist()
    df_raw = get_live_snapshot()
    if df_raw.empty:
        return LlmResponse(report="No processes to analyse.")
    df = run_anomaly_detection(df_raw, model)
    # Use model flag directly; also exclude whitelisted names so LLM only sees real threats
    wl_set = set(whitelist)
    df_anomalies = df[df["is_anomaly"] & ~df["process_name"].isin(wl_set)]
    report = get_llm_explanation(df_anomalies, df)
    return LlmResponse(report=report)


# ── Serve built frontend (production mode) ────────────────────────────────────

if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        index = os.path.join(FRONTEND_DIST, "index.html")
        return FileResponse(index)


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
