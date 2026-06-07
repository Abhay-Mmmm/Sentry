"""
Session State Initialization
Configures application state defaults.
"""

import streamlit as st
import pandas as pd

def initialize_session_state():
    """Initialize all session state variables."""
    
    # Pre-populate historical threat reports for initial UI/UX presentation
    initial_reports = [
        {
            "Timestamp": (pd.Timestamp.now() - pd.to_timedelta(45, unit="m")).strftime("%Y-%m-%d %H:%M:%S"),
            "Threat Level": "High",
            "Process Count": 3,
            "Summary": "Analyzed 3 anomalies (Top: unknown_binary). CPU usage exceeds 70% threshold.",
            "Details": """# 🛡️ Sentinel AI Security Analysis Report
**Generated:** `2026-06-07 14:30:15` | **Scope:** Local Endpoint | **Model:** Gemma 2B (Cached)

## 📊 Threat Summary
- **Overall Threat Level:** 🟠 **HIGH**
- **Total Flagged Anomalies:** `3` process(es)
- **Critical Risks:** `0` | **High Risks:** `2` | **Medium/Low:** `1`

## 🔍 Detailed Analysis
### 🟠 Process: `unknown_binary` (PID: `10842`)
- **Telemetry Stats:** CPU Usage: `72.4%` | Memory: `45.2%` | Threads: `48`
- **AI Verdict:** Unexpected binary name combined with persistent CPU consumption. Suggestive of local resource abuse or unauthorized crypto mining activity.

### 🟡 Process: `svchost.exe` (PID: `412`)
- **Telemetry Stats:** CPU Usage: `12.1%` | Memory: `61.8%` | Threads: `82`
- **AI Verdict:** Genuine system process but exhibiting atypical memory allocation. Investigate potential DLL injection vectors.

## 🛡️ Recommended Action
1. Terminate or suspend PID `10842` immediately.
2. Conduct a deep memory integrity scan on PID `412` to inspect stack handles."""
        },
        {
            "Timestamp": (pd.Timestamp.now() - pd.to_timedelta(2, unit="h")).strftime("%Y-%m-%d %H:%M:%S"),
            "Threat Level": "Critical",
            "Process Count": 1,
            "Summary": "Analyzed 1 anomaly (Top: suspicious.exe). Risk score 92/100.",
            "Details": """# 🛡️ Sentinel AI Security Analysis Report
**Generated:** `2026-06-07 13:15:00` | **Scope:** Local Endpoint | **Model:** Gemma 2B (Cached)

## 📊 Threat Summary
- **Overall Threat Level:** 🔴 **CRITICAL**
- **Total Flagged Anomalies:** `1` process(es)

## 🔍 Detailed Analysis
### 🔴 Process: `suspicious.exe` (PID: `63204`)
- **Telemetry Stats:** CPU Usage: `94.1%` | Memory: `34.8%` | Threads: `102`
- **Risk Index:** `92/100`
- **AI Verdict:** Binary signature matches high-risk heuristics. The process exhibits abnormal thread creation rates (102 threads), indicating potential buffer injection attacks or shellcode execution.

## 🛡️ Recommended Action
1. **Isolate Endpoint:** Sever network connections immediately.
2. **Force Terminate:** Kill PID `63204` using Sentinel process tools."""
        }
    ]

    initial_timeline = [
        {
            "timestamp": pd.Timestamp.now() - pd.to_timedelta(3, unit="h"),
            "type": "System Action",
            "description": "Project Sentinel telemetry engine initialized."
        },
        {
            "timestamp": pd.Timestamp.now() - pd.to_timedelta(2.5, unit="h"),
            "type": "System Action",
            "description": "Isolation Forest model (Team 2) successfully loaded."
        },
        {
            "timestamp": pd.Timestamp.now() - pd.to_timedelta(2, unit="h"),
            "type": "Anomaly Detection",
            "description": "Isolation Forest flagged anomaly: `suspicious.exe` (Risk: 92/100, PID: 63204)"
        },
        {
            "timestamp": pd.Timestamp.now() - pd.to_timedelta(45, unit="m"),
            "type": "Anomaly Detection",
            "description": "Isolation Forest flagged anomalies: `unknown_binary` (Risk: 78/100, PID: 10842) and `svchost.exe` (Risk: 55/100, PID: 412)"
        }
    ]

    defaults = {
        "df_all": None,
        "df_anomalies": None,
        "threat_reports": initial_reports,
        "timeline_events": initial_timeline,
        "auto_refresh": False,
        "refresh_interval": 5,
        "ollama_model": "gemma",
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
