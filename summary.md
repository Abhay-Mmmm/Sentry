# Team 3 Summary — LLM Bridge

## Responsibility

Build the LLM bridge that accepts anomalous processes and generates a security analysis report using Gemma 4B via Ollama.

---

## Function Contract

```python
def get_llm_explanation(df_anomalies: pd.DataFrame, df_all: pd.DataFrame) -> str:
```

**Input:**
- `df_anomalies`: DataFrame containing flagged anomalous processes
- `df_all`: Original process snapshot for baseline context

**Output:**
- `str`: Human-readable security narrative (3-5 sentences)

---

## Implementation Details

### 1. Data Processing
- Extracts top 5 most anomalous processes (sorted by `anomaly_score`)
- Aggregates baseline statistics from `df_all`:
  - Total processes monitored
  - Average CPU, memory, network, disk usage
  - Max CPU and memory observed

### 2. Prompt Construction
- Structured prompt with two sections:
  - **Original Process Snapshot Summary** — baseline metrics
  - **Flagged Anomalous Processes** — detailed anomaly list
- Requests threat classification and investigation recommendations

### 3. Ollama Integration
- **Endpoint**: `http://localhost:11434/api/generate`
- **Model**: `gemma4:e4b`
- **Timeout**: 120 seconds
- **Mode**: Non-streaming (`"stream": False`)

### 4. Error Handling
- Connection errors → Returns descriptive error string
- Timeouts → Returns timeout message
- Empty responses → Returns error message
- Never raises exceptions (always returns string)

---

## Usage

```python
# Inside render_dashboard()
if st.button("Explain Anomalies with Gemma 4B"):
    with st.spinner("Querying local LLM..."):
        explanation = get_llm_explanation(df_anomalies, df_all)
        st.session_state["llm_response"] = explanation

if "llm_response" in st.session_state:
    st.subheader("LLM Security Analysis")
    st.info(st.session_state["llm_response"])
```

---

## Performance Notes

| Model | VRAM | Inference Time | Hardware |
|-------|------|----------------|----------|
| `gemma2:2b` | ~2GB | 10-20s | GPU (RTX 4050) |
| `gemma4:e4b` | ~9.5GB | 2-5 min | CPU fallback |

For faster inference on RTX 4050 (6GB VRAM), use `gemma2:2b`.

---

## Files

| File | Purpose |
|------|---------|
| `app.py` | Main pipeline with LLM bridge integration |
| `model.pkl` | Pre-trained Isolation Forest |
| `requirements.txt` | Python dependencies |
| `.venv/` | Virtual environment |

---

## Running the Pipeline

```bash
cd /home/vander/Desktop/E/Projects/VSC/Sentry/Sentry
.venv/bin/streamlit run app.py
```

Open `http://localhost:8501` and click **"Explain Anomalies with Gemma 4B"**.
