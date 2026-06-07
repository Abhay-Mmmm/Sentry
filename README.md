# Project Sentinel — Local System Anomaly Monitor

> **Entirely offline. Zero cloud. One file. 60 minutes.**

A privacy-first process telemetry monitor that detects statistical anomalies using Isolation Forest and explains them in plain English using a locally hosted Gemma 2B LLM via Ollama. Runs on any workstation with Python 3.10+ and an RTX 4050 (or equivalent GPU with ≥4GB VRAM).

---

## Quick Start

### 1. Install Python dependencies

```bash
pip install streamlit scikit-learn requests pandas numpy
```

### 2. Pull the LLM model via Ollama

```bash
# Install Ollama first: https://ollama.com/download
ollama pull gemma2:2b
```

### 3. Verify Ollama is running

```bash
curl http://localhost:11434/api/tags
# Expected: JSON response listing available models
```

### 4. Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser. Click **Run Analysis** to generate telemetry, detect anomalies, and request an LLM explanation.

---

## The 60-Minute Battle Plan

```
TIMELINE      TEAM          TASK
──────────────────────────────────────────────────────────────────────────
00:00–00:10   ALL (6)       Environment Sync & Setup
00:10–00:45   Team 1 (2)    UI & Engine — render_dashboard()
              Team 2 (2)    Data & ML — generate_process_data() + run_anomaly_detection()
              Team 3 (2)    LLM Bridge — get_llm_explanation()
00:45–01:00   ASSEMBLER(1)  Paste all functions into app.py & run live demo
```

### Phase 1 — Environment Sync (00:00 → 00:10)

Every developer completes the following checklist before writing a single line of code:

- [ ] `python --version` — confirm Python ≥ 3.10
- [ ] `pip install streamlit scikit-learn requests pandas numpy` — confirm no errors
- [ ] `ollama pull gemma2:2b` — confirm model downloads (≈1.6 GB, do this first)
- [ ] `curl http://localhost:11434/api/tags` — confirm Ollama daemon is responding
- [ ] Clone/share the starter file with the shared constants block (see below)
- [ ] Verbally confirm variable names: **`df_all`**, **`df_anomalies`** — these are the only handoff variables

> **Critical:** All three teams must agree on the exact function signatures before minute 10. Do not start coding until the team lead reads the contracts aloud.

---

### Phase 2 — Parallel Code Sprint (00:10 → 00:45)

Each team works in a completely isolated Python file. No shared files during this phase. The only rule: **match the function signatures exactly as specified in the contracts below.**

---

### Phase 3 — Assembly & Live Demo (00:45 → 01:00)

One designated assembler takes all three files and pastes the functions into `app.py` in order. See the Assembly Protocol section below.

---

## Shared Constants Block

Every team file must begin with this identical block. Copy it verbatim.

```python
import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta
import random

# ── Shared Constants ──────────────────────────────────────────────────────────
N_SAMPLES        = 500
CONTAMINATION    = 0.05
OLLAMA_URL       = "http://localhost:11434/api/generate"
OLLAMA_MODEL     = "gemma2:2b"
FEATURE_COLUMNS  = ["cpu_percent", "memory_mb", "net_bytes_sent", "disk_read_ops"]
TOP_N_ANOMALIES  = 5  # rows sent to LLM for explanation
```

---

## Team Breakdown & Software Contracts

### Team 1 — UI & Engine

**File during sprint:** `team1_ui.py`

**Responsibility:** Build the Streamlit dashboard. Accept `df_all` and `df_anomalies` as function parameters. Trigger the LLM explanation on button click.

**Contract:**

```python
def render_dashboard(df_all: pd.DataFrame, df_anomalies: pd.DataFrame) -> None:
    """
    Renders the full Streamlit UI.

    Layout:
      - st.title: "Project Sentinel — Local Anomaly Monitor"
      - st.metric row: Total Processes | Anomalies Detected | Anomaly Rate %
      - st.subheader: "All Process Telemetry" + st.dataframe(df_all)
      - st.subheader: "Flagged Anomalies" + st.dataframe(df_anomalies, use_container_width=True)
      - st.button: "Explain Anomalies with Gemma 2B"
        - On click: call get_llm_explanation(df_anomalies)
        - Display result in st.info() with a header "LLM Security Analysis"

    Input:
      df_all        : pd.DataFrame  — 500 rows, full telemetry + anomaly columns
      df_anomalies  : pd.DataFrame  — ~25 rows, anomalous subset of df_all

    Output:
      None (Streamlit side-effects only)
    """
    pass  # replace with implementation
```

**Key rules for Team 1:**
- Do NOT call `generate_process_data()` or `run_anomaly_detection()` — those belong to Team 2.
- Do NOT call `get_llm_explanation()` except inside the button handler.
- Use `st.session_state["llm_response"]` to cache the LLM response so it survives re-runs.
- Highlight anomaly rows: apply `df_all.style.apply(lambda row: ['background-color: #ffe0e0' if row['is_anomaly'] else '' for _ in row], axis=1)` before passing to `st.dataframe`.

**Minimal skeleton:**

```python
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

    if st.button("Explain Anomalies with Gemma 2B"):
        with st.spinner("Querying local LLM..."):
            explanation = get_llm_explanation(df_anomalies)
            st.session_state["llm_response"] = explanation

    if "llm_response" in st.session_state:
        st.subheader("LLM Security Analysis")
        st.info(st.session_state["llm_response"])
```

---

### Team 2 — Data & ML

**File during sprint:** `team2_data.py`

**Responsibility:** Generate synthetic process telemetry with injected anomalies. Fit and apply an Isolation Forest model. Return `df_all` and `df_anomalies`.

**Contract:**

```python
def generate_process_data(n_samples: int = N_SAMPLES) -> pd.DataFrame:
    """
    Generates synthetic process telemetry with realistic distributions.
    Injects anomaly signatures into ~5% of rows before returning.

    Anomaly signatures to inject (mix randomly):
      - CPU spike:    cpu_percent = np.random.uniform(90, 100)
      - Memory leak:  memory_mb   = np.random.uniform(3500, 4096)
      - Net silence:  net_bytes_sent = 0.0  (combined with high CPU)
      - Disk storm:   disk_read_ops = np.random.uniform(900, 1000)

    Returns:
      pd.DataFrame with columns:
        timestamp, process_name, pid, cpu_percent,
        memory_mb, net_bytes_sent, disk_read_ops
      (NO anomaly_score or is_anomaly — those are added by run_anomaly_detection)
    """
    pass

def run_anomaly_detection(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fits an IsolationForest on FEATURE_COLUMNS of df.
    Appends two columns to df:
      - anomaly_score : float  (raw score; more negative = more anomalous)
      - is_anomaly    : bool   (True for the contamination fraction)

    Returns:
      (df_all, df_anomalies)
      df_all       : the full DataFrame with appended columns
      df_anomalies : filtered subset where is_anomaly == True
    """
    pass
```

**Key rules for Team 2:**
- `df_all` must have **all 9 columns** in the exact order listed in the data contract.
- `df_anomalies` is strictly `df_all[df_all["is_anomaly"] == True].reset_index(drop=True)`.
- Do NOT rename any column. Do NOT drop any column. The assembler will not rename variables.
- Seed `np.random` with `42` for reproducibility: `np.random.seed(42)`.

**Minimal skeleton:**

```python
PROCESS_NAMES = [
    "chrome.exe", "python.exe", "node.exe", "svchost.exe",
    "code.exe", "explorer.exe", "docker.exe", "git.exe"
]

def generate_process_data(n_samples: int = N_SAMPLES) -> pd.DataFrame:
    np.random.seed(42)
    base_time = datetime.utcnow() - timedelta(minutes=n_samples)

    records = []
    for i in range(n_samples):
        record = {
            "timestamp":      base_time + timedelta(seconds=i * 6),
            "process_name":   random.choice(PROCESS_NAMES),
            "pid":            random.randint(100, 9999),
            "cpu_percent":    np.random.normal(loc=25, scale=15).clip(0, 85),
            "memory_mb":      np.random.normal(loc=512, scale=200).clip(50, 3000),
            "net_bytes_sent": np.random.exponential(scale=50000).clip(0, 800000),
            "disk_read_ops":  np.random.normal(loc=50, scale=30).clip(0, 850),
        }
        records.append(record)

    # Inject anomalies into ~5% of rows
    anomaly_indices = np.random.choice(n_samples, size=int(n_samples * 0.05), replace=False)
    for idx in anomaly_indices:
        anomaly_type = random.choice(["cpu_spike", "memory_leak", "net_silence", "disk_storm"])
        if anomaly_type == "cpu_spike":
            records[idx]["cpu_percent"] = np.random.uniform(90, 100)
        elif anomaly_type == "memory_leak":
            records[idx]["memory_mb"] = np.random.uniform(3500, 4096)
        elif anomaly_type == "net_silence":
            records[idx]["net_bytes_sent"] = 0.0
            records[idx]["cpu_percent"] = np.random.uniform(88, 99)
        elif anomaly_type == "disk_storm":
            records[idx]["disk_read_ops"] = np.random.uniform(900, 1000)

    return pd.DataFrame(records)


def run_anomaly_detection(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    model = IsolationForest(contamination=CONTAMINATION, random_state=42, n_jobs=-1)
    X = df[FEATURE_COLUMNS].values
    df = df.copy()
    df["anomaly_score"] = model.fit_predict(X).astype(float)
    df["anomaly_score"] = model.score_samples(X)
    df["is_anomaly"]    = model.fit_predict(X) == -1
    df_anomalies        = df[df["is_anomaly"]].reset_index(drop=True)
    return df, df_anomalies
```

---

### Team 3 — LLM Bridge

**File during sprint:** `team3_llm.py`

**Responsibility:** Accept `df_anomalies`, construct a structured security analysis prompt, POST it to Ollama, and return a plain English explanation string.

**Contract:**

```python
def get_llm_explanation(df_anomalies: pd.DataFrame) -> str:
    """
    Constructs a security analysis prompt from the top TOP_N_ANOMALIES rows
    of df_anomalies (sorted by anomaly_score ascending = most anomalous first).

    Sends a synchronous POST to OLLAMA_URL with OLLAMA_MODEL.
    Parses the response and returns the LLM's narrative as a plain string.

    If Ollama is unreachable or returns an error, returns a descriptive
    error string (does NOT raise an exception).

    Input:
      df_anomalies : pd.DataFrame — anomalous rows with all df_all columns

    Output:
      str — LLM security narrative (3–6 sentences) or error message string
    """
    pass
```

**Key rules for Team 3:**
- Never raise exceptions — catch all errors and return them as strings. The UI depends on a string return type unconditionally.
- Use `"stream": False` in the Ollama payload to get a single JSON response object, not a stream.
- The response key is `response["response"]` (not `response["text"]` or `response["content"]`).
- Keep the prompt under 800 tokens. Use only the top `TOP_N_ANOMALIES` rows.
- Timeout the request at 120 seconds: `requests.post(..., timeout=120)`.

**Minimal skeleton:**

```python
def get_llm_explanation(df_anomalies: pd.DataFrame) -> str:
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

        prompt = f"""You are a cybersecurity analyst reviewing system process anomalies detected by an Isolation Forest model.

The following processes have been flagged as statistically anomalous based on CPU, memory, network, and disk activity:

{anomaly_block}

Provide a concise security analysis (3–5 sentences) that:
1. Identifies the most concerning anomaly pattern and the likely threat class (e.g., cryptominer, data exfiltration, runaway process, ransomware staging).
2. Explains why the specific metric values are suspicious.
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
```

---

## Assembly Protocol

At minute 45, the designated assembler creates `app.py` by following these steps in order. No other team member touches this file.

### Step 1 — Create `app.py` with the shared constants block

```python
# app.py — Project Sentinel (assembled at minute 45)

import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import IsolationForest
from datetime import datetime, timedelta
import random

# ── Shared Constants ──────────────────────────────────────────────────────────
N_SAMPLES        = 500
CONTAMINATION    = 0.05
OLLAMA_URL       = "http://localhost:11434/api/generate"
OLLAMA_MODEL     = "gemma2:2b"
FEATURE_COLUMNS  = ["cpu_percent", "memory_mb", "net_bytes_sent", "disk_read_ops"]
TOP_N_ANOMALIES  = 5
PROCESS_NAMES    = [
    "chrome.exe", "python.exe", "node.exe", "svchost.exe",
    "code.exe", "explorer.exe", "docker.exe", "git.exe"
]
```

### Step 2 — Paste Team 2's functions (data + ML)

Paste the full body of `generate_process_data()` and `run_anomaly_detection()` from `team2_data.py`, below the constants block.

### Step 3 — Paste Team 3's function (LLM bridge)

Paste the full body of `get_llm_explanation()` from `team3_llm.py`, below Team 2's functions.

### Step 4 — Paste Team 1's function (UI)

Paste the full body of `render_dashboard()` from `team1_ui.py`, below Team 3's function.

### Step 5 — Add the `main()` orchestrator and entry point

```python
def main():
    st.set_page_config(page_title="Project Sentinel", layout="wide")
    df_raw = generate_process_data(n_samples=N_SAMPLES)
    df_all, df_anomalies = run_anomaly_detection(df_raw)
    render_dashboard(df_all, df_anomalies)

if __name__ == "__main__":
    main()
```

### Step 6 — Run and verify

```bash
streamlit run app.py
```

**Assembly checklist:**
- [ ] Only one `import` block at the top (the shared constants block)
- [ ] No duplicate function definitions
- [ ] Variable names match exactly: `df_all`, `df_anomalies`, `df_raw`
- [ ] `render_dashboard` is called **after** both DataFrames are created
- [ ] `get_llm_explanation` is **not** called in `main()` — only inside the button handler in `render_dashboard`

---

## Variable Name Reference Card

Pin this to your screen during the sprint. These names must be byte-for-byte identical across all three teams.

| Variable | Type | Owner | Consumers |
|---|---|---|---|
| `df_raw` | `pd.DataFrame` | Team 2 (`generate_process_data` return) | Team 2 (`run_anomaly_detection` input) |
| `df_all` | `pd.DataFrame` | Team 2 (`run_anomaly_detection` return[0]) | Team 1 (`render_dashboard` param) |
| `df_anomalies` | `pd.DataFrame` | Team 2 (`run_anomaly_detection` return[1]) | Team 1 (display), Team 3 (LLM input) |
| `FEATURE_COLUMNS` | `list[str]` | Shared constants | Team 2 (ML fit) |
| `TOP_N_ANOMALIES` | `int` | Shared constants | Team 3 (prompt construction) |
| `OLLAMA_URL` | `str` | Shared constants | Team 3 (HTTP target) |
| `OLLAMA_MODEL` | `str` | Shared constants | Team 3 (model selector) |

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Connection refused` on LLM button | Ollama not running | Run `ollama serve` in a separate terminal |
| `model not found` error in LLM response | Gemma not pulled | Run `ollama pull gemma2:2b` |
| Streamlit re-runs on every click resetting LLM response | Not using session_state | Ensure `st.session_state["llm_response"]` pattern is used |
| `KeyError: 'is_anomaly'` in `render_dashboard` | `run_anomaly_detection` not appending column | Verify Team 2's function returns `df_all` with `is_anomaly` column |
| `TypeError` in `run_anomaly_detection` | Wrong column names in `FEATURE_COLUMNS` | Cross-check against the exact column names in `generate_process_data` |
| LLM response is empty string | Ollama returned `{"response": ""}` | Model still loading; click button again after 10 seconds |
| VRAM OOM error | Running a model too large for GPU | Confirm `gemma2:2b` is selected, not `gemma2:9b` or larger |

---

## Project Structure

```
sentry/
├── app.py              # Final assembled monolith (created at minute 45)
├── team1_ui.py         # Team 1 working file (discarded after assembly)
├── team2_data.py       # Team 2 working file (discarded after assembly)
├── team3_llm.py        # Team 3 working file (discarded after assembly)
├── PRD.md              # Product Requirements Document
└── README.md           # This file
```

---

## License

MIT — built in 60 minutes, ship it.
