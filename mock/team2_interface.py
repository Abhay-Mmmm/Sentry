"""
Mock Team 2 Integration - Anomaly Detection Interface
Provides df_all and df_anomalies with fallbacks.
"""

import pandas as pd
import numpy as np
import os
import random

# Try importing the real Team 2 module
try:
    import importlib.util
    spec = importlib.util.find_spec("team2_module")
    if spec is not None:
        from team2_module import get_anomalies
        USE_MOCK = False
    else:
        USE_MOCK = True
except ImportError:
    USE_MOCK = True

def generate_mock_data(n_processes=1000, anomaly_rate=0.05):
    """Generate realistic mock process data with anomalies."""
    np.random.seed(42)
    pids = np.random.randint(1000, 65535, n_processes)
    process_names = np.random.choice(
        ["chrome.exe", "python.exe", "svchost.exe", "explorer.exe", "firefox.exe",
         "node.exe", "docker.exe", "systemd", "nginx", "mysql.exe",
         " unidentified_process", "unknown_binary", "suspicious.exe", "malware_sample"],
        n_processes,
        p=[0.20, 0.15, 0.10, 0.08, 0.08, 0.07, 0.06, 0.05, 0.05, 0.05, 0.04, 0.03, 0.03, 0.01]
    )

    threads = np.random.poisson(15, n_processes)
    cpu = np.random.beta(2, 5, n_processes) * 100
    memory = np.random.beta(2, 7, n_processes) * 100

    # Flag anomalies with higher CPU/Memory/Threads
    is_anomaly = np.zeros(n_processes, dtype=bool)
    anomaly_indices = np.random.choice(n_processes, size=int(n_processes * anomaly_rate), replace=False)
    is_anomaly[anomaly_indices] = True

    cpu[anomaly_indices] = np.clip(cpu[anomaly_indices] + np.random.uniform(30, 60, len(anomaly_indices)), 0, 100)
    memory[anomaly_indices] = np.clip(memory[anomaly_indices] + np.random.uniform(20, 50, len(anomaly_indices)), 0, 100)
    threads[anomaly_indices] += np.random.randint(20, 100, len(anomaly_indices))

    df_all = pd.DataFrame({
        "PID": pids,
        "Process": process_names,
        "CPU (%)": np.round(cpu, 2),
        "Memory (%)": np.round(memory, 2),
        "Threads": threads,
        "Status": np.where(is_anomaly, "Anomaly", "Normal"),
        "is_anomaly": is_anomaly,
        "Risk Score": np.where(is_anomaly, np.random.randint(70, 100, n_processes), np.random.randint(0, 40, n_processes)),
        "Detection Time": pd.Timestamp.now() - pd.to_timedelta(np.random.randint(0, 3600, n_processes), unit="s"),
    })

    df_anomalies = df_all[df_all["Status"] == "Anomaly"].reset_index(drop=True)
    return df_all, df_anomalies

import streamlit as st

def get_anomalies():
    """
    Integration point: receives data from Team 2.
    Falls back to mock data if Team 2 is unavailable.
    """
    if not USE_MOCK:
        try:
            from team2_module import get_anomalies as real_get_anomalies
            df_all, df_anom = real_get_anomalies()
            if "is_anomaly" not in df_all.columns:
                df_all["is_anomaly"] = (df_all["Status"] == "Anomaly") if "Status" in df_all.columns else False
            return df_all, df_anom
        except Exception:
            pass

    # Mock data generation with state-based drift
    if "base_df_all" not in st.session_state or st.session_state.get("rescan_trigger", False):
        df_all, _ = generate_mock_data()
        st.session_state["base_df_all"] = df_all
        st.session_state["rescan_trigger"] = False
        
    df = st.session_state["base_df_all"].copy()
    n = len(df)
    
    # Introduce small random variations to make metrics drift realistically
    cpu_drift = np.random.uniform(-1.5, 1.5, n)
    mem_drift = np.random.uniform(-0.5, 0.5, n)
    
    df["CPU (%)"] = np.clip(df["CPU (%)"] + cpu_drift, 0.0, 100.0).round(2)
    df["Memory (%)"] = np.clip(df["Memory (%)"] + mem_drift, 0.0, 100.0).round(2)
    
    # Re-extract anomalies based on updated status
    df_anomalies = df[df["Status"] == "Anomaly"].reset_index(drop=True)
    return df, df_anomalies
