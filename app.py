# app.py — Project Sentinel: Team 3 Pipeline

import streamlit as st
import pandas as pd
import numpy as np
import requests
import joblib
from datetime import datetime, timedelta
import random

# ── Shared Constants ──────────────────────────────────────────────────────────
N_SAMPLES        = 500
OLLAMA_URL       = "http://localhost:11434/api/generate"
OLLAMA_MODEL     = "gemma4:e4b"
FEATURE_COLUMNS  = ["cpu_percent", "memory_mb", "net_bytes_sent", "disk_read_ops"]
TOP_N_ANOMALIES  = 5
MODEL_PATH       = "model.pkl"
PROCESS_NAMES    = [
    "chrome.exe", "python.exe", "node.exe", "svchost.exe",
    "code.exe", "explorer.exe", "docker.exe", "git.exe"
]


# ── Team 2: Data Generation ───────────────────────────────────────────────────
def generate_process_data(n_samples: int = N_SAMPLES) -> pd.DataFrame:
    np.random.seed(42)
    base_time = datetime.utcnow() - timedelta(minutes=n_samples)

    records = []
    for i in range(n_samples):
        record = {
            "timestamp":      base_time + timedelta(seconds=i * 6),
            "process_name":   random.choice(PROCESS_NAMES),
            "pid":            random.randint(100, 9999),
            "cpu_percent":    float(np.clip(np.random.normal(loc=25, scale=15), 0, 85)),
            "memory_mb":      float(np.clip(np.random.normal(loc=512, scale=200), 50, 3000)),
            "net_bytes_sent": float(np.clip(np.random.exponential(scale=50000), 0, 800000)),
            "disk_read_ops":  float(np.clip(np.random.normal(loc=50, scale=30), 0, 850)),
        }
        records.append(record)

    # Inject anomalies into ~5% of rows
    anomaly_indices = np.random.choice(n_samples, size=int(n_samples * 0.05), replace=False)
    for idx in anomaly_indices:
        anomaly_type = random.choice(["cpu_spike", "memory_leak", "net_silence", "disk_storm"])
        if anomaly_type == "cpu_spike":
            records[idx]["cpu_percent"] = float(np.random.uniform(90, 100))
        elif anomaly_type == "memory_leak":
            records[idx]["memory_mb"] = float(np.random.uniform(3500, 4096))
        elif anomaly_type == "net_silence":
            records[idx]["net_bytes_sent"] = 0.0
            records[idx]["cpu_percent"] = float(np.random.uniform(88, 99))
        elif anomaly_type == "disk_storm":
            records[idx]["disk_read_ops"] = float(np.random.uniform(900, 1000))

    return pd.DataFrame(records)


# ── Team 2: Anomaly Detection with Pre-trained Model ──────────────────────────
def run_anomaly_detection(df: pd.DataFrame, model) -> tuple[pd.DataFrame, pd.DataFrame]:
    X = df[FEATURE_COLUMNS].values
    df = df.copy()
    df["anomaly_score"] = model.score_samples(X)
    df["is_anomaly"] = model.predict(X) == -1
    df_anomalies = df[df["is_anomaly"]].reset_index(drop=True)
    return df, df_anomalies


# ── Team 3: LLM Bridge ────────────────────────────────────────────────────────
def get_llm_explanation(df_anomalies: pd.DataFrame, df_all: pd.DataFrame) -> str:
    try:
        top_anomalies = df_anomalies.nsmallest(TOP_N_ANOMALIES, "anomaly_score")

        anomaly_lines = []
        for _, row in top_anomalies.iterrows():
            anomaly_lines.append(
                f"- Process: {row['process_name']} (PID {row['pid']}) | "
                f"CPU: {row['cpu_percent']:.1f}% | "
                f"Memory: {row['memory_mb']:.0f}MB | "
                f"Net Sent: {row['net_bytes_sent']:.0f} bytes | "
                f"Disk Ops: {row['disk_read_ops']:.0f}/s | "
                f"Anomaly Score: {row['anomaly_score']:.4f}"
            )

        anomaly_block = "\n".join(anomaly_lines)

        # Aggregate stats from original process snapshot
        total_processes = len(df_all)
        avg_cpu = df_all["cpu_percent"].mean()
        avg_memory = df_all["memory_mb"].mean()
        avg_net = df_all["net_bytes_sent"].mean()
        avg_disk = df_all["disk_read_ops"].mean()
        max_cpu = df_all["cpu_percent"].max()
        max_memory = df_all["memory_mb"].max()

        snapshot_summary = f"""Total Processes Monitored: {total_processes}
Average CPU Usage: {avg_cpu:.1f}%
Average Memory Usage: {avg_memory:.0f}MB
Average Network Bytes Sent: {avg_net:.0f}
Average Disk Read Ops: {avg_disk:.0f}/s
Max CPU Observed: {max_cpu:.1f}%
Max Memory Observed: {max_memory:.0f}MB"""

        prompt = f"""You are a cybersecurity analyst reviewing system process anomalies detected by an Isolation Forest model.

## Original Process Snapshot Summary:
{snapshot_summary}

## Flagged Anomalous Processes:
{anomaly_block}

Provide a concise security analysis (3–5 sentences) that:
1. Identifies the most concerning anomaly pattern and the likely threat class (e.g., cryptominer, data exfiltration, runaway process, ransomware staging).
2. Explains why the specific metric values are suspicious compared to the baseline.
3. Recommends an immediate investigation step a sysadmin should take.

Be specific and direct. Do not hedge with 'may' or 'could' — state your assessment confidently."""

        payload = {
            "model":  OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "Error: empty response from LLM.")

    except requests.exceptions.ConnectionError:
        return "Error: Cannot reach Ollama at localhost:11434. Ensure 'ollama serve' is running."
    except requests.exceptions.Timeout:
        return "Error: Ollama request timed out after 120 seconds. Model may be loading — try again."
    except Exception as e:
        return f"Error: Unexpected failure in LLM bridge — {str(e)}"


# ── Team 1: UI Dashboard ──────────────────────────────────────────────────────
def render_dashboard(df_all: pd.DataFrame, df_anomalies: pd.DataFrame) -> None:
    st.title("Project Sentinel — Local Anomaly Monitor")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Processes", len(df_all))
    col2.metric("Anomalies Detected", len(df_anomalies))
    col3.metric("Anomaly Rate", f"{len(df_anomalies)/len(df_all)*100:.1f}%")

    st.subheader("All Process Telemetry")
    st.dataframe(df_all, use_container_width=True)

    st.subheader("Flagged Anomalies")
    st.dataframe(df_anomalies, use_container_width=True)

    if st.button("Explain Anomalies with Gemma 4B"):
        with st.spinner("Querying local LLM..."):
            explanation = get_llm_explanation(df_anomalies, df_all)
            st.session_state["llm_response"] = explanation

    if "llm_response" in st.session_state:
        st.subheader("LLM Security Analysis")
        st.info(st.session_state["llm_response"])


# ── Main Orchestrator ─────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="Project Sentinel", layout="wide")

    # Load pre-trained model
    try:
        model = joblib.load(MODEL_PATH)
    except FileNotFoundError:
        st.error(f"Model file '{MODEL_PATH}' not found. Please ensure the Isolation Forest model is available.")
        return

    # Generate demo data
    df_raw = generate_process_data(n_samples=N_SAMPLES)

    # Run anomaly detection
    df_all, df_anomalies = run_anomaly_detection(df_raw, model)

    # Render dashboard
    render_dashboard(df_all, df_anomalies)


if __name__ == "__main__":
    main()
