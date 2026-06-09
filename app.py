# app.py — Project Sentinel

import json
import os
import time
from datetime import datetime, timezone

import joblib
import pandas as pd
import plotly.express as px
import psutil
import requests
import streamlit as st

OLLAMA_URL      = "http://localhost:11434/api/generate"
OLLAMA_MODEL    = "gemma4:e4b"
FEATURE_COLUMNS = ["cpu_percent", "memory_mb", "net_bytes_sent", "disk_read_ops"]
TOP_N_ANOMALIES = 5
MODEL_PATH      = "model.pkl"
WHITELIST_PATH  = "whitelist.json"


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
            procs_before[p.pid] = {"proc": p, "io_read": io.read_count,
                                   "io_write": io.write_count,
                                   "conns": len(p.net_connections())}
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
                "timestamp": ts, "process_name": info["name"], "pid": pid,
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


def run_anomaly_detection(df: pd.DataFrame, model, whitelist: set) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    df["anomaly_score"] = model.score_samples(df[FEATURE_COLUMNS].values)
    df["is_anomaly"]    = model.predict(df[FEATURE_COLUMNS].values) == -1
    # status: "normal" | "anomaly" | "whitelisted"
    df["status"] = df.apply(
        lambda r: "whitelisted" if (r["is_anomaly"] and r["process_name"] in whitelist)
                  else ("anomaly" if r["is_anomaly"] else "normal"),
        axis=1,
    )
    df_anomalies = df[df["status"] == "anomaly"].reset_index(drop=True)
    return df, df_anomalies


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


CSS = """
<style>
/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', system-ui, sans-serif;
}
[data-testid="stSidebar"] { background-color: #161b22; }
[data-testid="stHeader"]  { background-color: #0d1117; }

/* ── Title ── */
h1 { 
    color: #58a6ff !important;
    font-size: 2.4rem !important;
    letter-spacing: 0.04em;
    border-bottom: 2px solid #21262d;
    padding-bottom: 0.5rem;
}
h2, h3 { color: #79c0ff !important; font-size: 1.3rem !important; }

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 1rem 1.2rem;
}
[data-testid="stMetricLabel"]  { color: #8b949e !important; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; }
[data-testid="stMetricValue"]  { color: #e6edf3 !important; font-size: 1.8rem !important; font-weight: 700; }
[data-testid="stMetricDelta"]  { color: #3fb950 !important; }

/* ── Buttons ── */
[data-testid="stButton"] > button {
    background: #21262d;
    color: #e6edf3;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 0.5rem 1.2rem;
    font-weight: 600;
    transition: all 0.2s;
}
[data-testid="stButton"] > button:hover {
    background: #388bfd22;
    border-color: #58a6ff;
    color: #58a6ff;
}

/* ── Tabs ── */
[data-testid="stTabs"] button {
    color: #8b949e !important;
    font-weight: 600;
    font-size: 1rem;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #58a6ff !important;
    border-bottom: 2px solid #58a6ff !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid #21262d; border-radius: 8px; }
iframe { background: #161b22 !important; }

/* ── Info / LLM box ── */
[data-testid="stAlert"] {
    background: #0d2137 !important;
    border: 1px solid #1f6feb !important;
    border-radius: 10px;
    color: #cdd9e5 !important;
    font-size: 0.875rem;
    line-height: 1.7;
}

/* ── Divider ── */
hr { border-color: #21262d !important; }

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #58a6ff !important; }

/* ── Anomaly badge in subheader ── */
.anomaly-count {
    display: inline-block;
    background: #da36363d;
    color: #f85149;
    border: 1px solid #f8514944;
    border-radius: 20px;
    padding: 0.1rem 0.7rem;
    font-size: 0.85rem;
    font-weight: 700;
    margin-left: 0.5rem;
    vertical-align: middle;
}
.section-label {
    font-size: 0.75rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.3rem;
}
</style>
"""

CHART_THEME = dict(
    paper_bgcolor="#161b22",
    plot_bgcolor="#161b22",
    font=dict(color="#8b949e", family="Segoe UI, system-ui, sans-serif"),
    title_font=dict(color="#79c0ff", size=14),
    xaxis=dict(gridcolor="#21262d", zerolinecolor="#21262d", color="#8b949e"),
    yaxis=dict(gridcolor="#21262d", zerolinecolor="#21262d", color="#8b949e"),
    legend=dict(bgcolor="#0d1117", bordercolor="#21262d", borderwidth=1),
    margin=dict(t=45, b=20, l=10, r=10),
)


def main():
    st.set_page_config(page_title="Project Sentinel", layout="wide", page_icon="🛡️")
    st.markdown(CSS, unsafe_allow_html=True)

    st.title("🛡️ Project Sentinel — Live Anomaly Monitor")
    st.markdown('<p class="section-label">Isolation Forest · Real-time process telemetry · Local LLM analysis</p>', unsafe_allow_html=True)

    try:
        model = joblib.load(MODEL_PATH)
    except FileNotFoundError:
        st.error(f"'{MODEL_PATH}' not found. Run `python ml_pipeline.py` first.")
        return

    # ── Snapshot once per session ─────────────────────────────────────────────
    whitelist = load_whitelist()

    if "df_all" not in st.session_state:
        with st.spinner("📡 Taking live process snapshot (1s)..."):
            df_raw = get_live_snapshot()
            df_all, df_anomalies = run_anomaly_detection(df_raw, model, whitelist)
            st.session_state["df_all"] = df_all
            st.session_state["df_anomalies"] = df_anomalies

    df_all       = st.session_state["df_all"]
    df_anomalies = st.session_state["df_anomalies"]

    if st.button("🔄 Refresh Snapshot"):
        for k in ["df_all", "df_anomalies", "llm_response"]:
            st.session_state.pop(k, None)
        st.rerun()

    # ── Metrics row ───────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    n_whitelisted = (df_all["status"] == "whitelisted").sum()
    anomaly_rate = len(df_anomalies) / len(df_all) * 100
    c1.metric("🖥️  Processes Monitored", len(df_all))
    c2.metric("🚨  Anomalies Detected",  len(df_anomalies))
    c3.metric("📊  Anomaly Rate",        f"{anomaly_rate:.1f}%",
              delta="above threshold" if anomaly_rate > 10 else "within normal range",
              delta_color="inverse" if anomaly_rate > 10 else "normal")
    c4.metric("✅  Whitelisted",         n_whitelisted)

    st.divider()

    # ── Charts row ────────────────────────────────────────────────────────────
    STATUS_COLORS = {"normal": "#3fb950", "anomaly": "#f85149", "whitelisted": "#e3b341"}

    col_pie, col_bar = st.columns(2)

    with col_pie:
        pie_counts = df_all["status"].value_counts().reset_index()
        pie_counts.columns = ["Status", "Count"]
        pie_counts["Status"] = pie_counts["Status"].map(
            {"normal": "✓ Normal", "anomaly": "⚠ Anomaly", "whitelisted": "~ Whitelisted"})
        fig_pie = px.pie(
            pie_counts, names="Status", values="Count",
            color="Status",
            color_discrete_map={"✓ Normal": "#3fb950", "⚠ Anomaly": "#f85149", "~ Whitelisted": "#e3b341"},
            title="Process Health Overview",
        )
        fig_pie.update_traces(
            textinfo="label+percent",
            textposition="outside",
            textfont=dict(color="#e6edf3", size=11),
            marker=dict(line=dict(color="#0d1117", width=2)),
            pull=0.02,
        )
        fig_pie.update_layout(**CHART_THEME, showlegend=False,
                              uniformtext_minsize=10, uniformtext_mode="hide")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        top_cpu = df_all.nlargest(10, "cpu_percent").copy()
        top_cpu["label"] = top_cpu["process_name"] + "  (" + top_cpu["pid"].astype(str) + ")"
        top_cpu["Status"] = top_cpu["status"].map(
            {"normal": "✓ Normal", "anomaly": "⚠ Anomaly", "whitelisted": "~ Whitelisted"})
        fig_bar = px.bar(
            top_cpu, x="cpu_percent", y="label", orientation="h",
            color="Status",
            color_discrete_map={"✓ Normal": "#388bfd", "⚠ Anomaly": "#f85149", "~ Whitelisted": "#e3b341"},
            labels={"cpu_percent": "CPU %", "label": "", "Status": ""},
            title="Top 10 Processes by CPU",
        )
        fig_bar.update_layout(**CHART_THEME)
        fig_bar.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Scatter ───────────────────────────────────────────────────────────────
    df_all["Status"] = df_all["status"].map(
        {"normal": "✓ Normal", "anomaly": "⚠ Anomaly", "whitelisted": "~ Whitelisted"})
    fig_scatter = px.scatter(
        df_all, x="cpu_percent", y="memory_mb",
        color="Status",
        color_discrete_map={"✓ Normal": "#3fb950", "⚠ Anomaly": "#f85149", "~ Whitelisted": "#e3b341"},
        hover_data=["process_name", "pid", "disk_read_ops", "net_bytes_sent", "anomaly_score"],
        labels={"cpu_percent": "CPU %", "memory_mb": "Memory (MB)", "Status": ""},
        title="CPU vs Memory (hover for details)",
        opacity=0.8,
    )
    fig_scatter.update_traces(marker=dict(size=9, line=dict(width=1, color="#0d1117")))
    fig_scatter.update_layout(**CHART_THEME)
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.divider()

    # ── Tables ────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["🚨 Flagged Anomalies", "📋 All Processes", "✅ Whitelist"])

    with tab1:
        st.markdown(f'<p class="section-label">Sorted by anomaly score · most severe first <span class="anomaly-count">{len(df_anomalies)} flagged</span></p>', unsafe_allow_html=True)
        display_cols = ["process_name", "pid", "cpu_percent", "memory_mb",
                        "net_bytes_sent", "disk_read_ops", "anomaly_score"]

        if len(df_anomalies):
            # Checklist: one checkbox per unique anomalous process name
            st.markdown('<p class="section-label">Select processes to grant normal status</p>', unsafe_allow_html=True)
            unique_anomalies = sorted(df_anomalies["process_name"].unique())
            checked = []
            cols = st.columns(min(3, len(unique_anomalies)))
            for i, name in enumerate(unique_anomalies):
                if cols[i % 3].checkbox(name, key=f"wl_{name}"):
                    checked.append(name)

            if checked:
                if st.button(f"✅ Ignore {len(checked)} process(es) as anomalies", type="primary"):
                    new_wl = whitelist | set(checked)
                    save_whitelist(new_wl)
                    for k in ["df_all", "df_anomalies"]:
                        st.session_state.pop(k, None)
                    st.success(f"Added to whitelist: {', '.join(checked)}. Refreshing...")
                    st.rerun()

            st.dataframe(
                df_anomalies[display_cols].sort_values("anomaly_score"),
                use_container_width=True, hide_index=True,
                column_config={
                    "process_name":   st.column_config.TextColumn("Process"),
                    "pid":            st.column_config.NumberColumn("PID", format="%d"),
                    "cpu_percent":    st.column_config.ProgressColumn("CPU %", min_value=0, max_value=100, format="%.1f%%"),
                    "memory_mb":      st.column_config.NumberColumn("Memory (MB)", format="%.1f"),
                    "net_bytes_sent": st.column_config.NumberColumn("Net Sent (B/s)", format="%.0f"),
                    "disk_read_ops":  st.column_config.NumberColumn("Disk Reads/s", format="%.0f"),
                    "anomaly_score":  st.column_config.NumberColumn("Anomaly Score", format="%.4f"),
                },
            )
        else:
            st.success("🎉 No active anomalies detected.")

        # Show whitelisted processes in this snapshot (yellow)
        df_wl_snap = df_all[df_all["status"] == "whitelisted"]
        if len(df_wl_snap):
            st.markdown('<p class="section-label" style="color:#e3b341">~ whitelisted (ignored anomalies)</p>', unsafe_allow_html=True)
            st.dataframe(df_wl_snap[display_cols].sort_values("anomaly_score"),
                         use_container_width=True, hide_index=True)

    with tab2:
        st.markdown('<p class="section-label">All monitored processes · sorted by anomaly score</p>', unsafe_allow_html=True)
        st.dataframe(
            df_all.drop(columns=["Status"]).sort_values("anomaly_score"),
            use_container_width=True, hide_index=True,
            column_config={
                "cpu_percent":  st.column_config.ProgressColumn("CPU %", min_value=0, max_value=100, format="%.1f%%"),
                "memory_mb":    st.column_config.NumberColumn("Memory (MB)", format="%.1f"),
                "status":       st.column_config.TextColumn("Status"),
                "anomaly_score":st.column_config.NumberColumn("Score", format="%.4f"),
            },
        )

    with tab3:
        st.markdown('<p class="section-label">Processes permanently ignored as anomalies · persisted in whitelist.json</p>', unsafe_allow_html=True)
        if whitelist:
            to_remove = []
            for name in sorted(whitelist):
                col_a, col_b = st.columns([4, 1])
                col_a.markdown(f"**{name}**")
                if col_b.button("Remove", key=f"rm_{name}"):
                    to_remove.append(name)
            if to_remove:
                new_wl = whitelist - set(to_remove)
                save_whitelist(new_wl)
                for k in ["df_all", "df_anomalies"]:
                    st.session_state.pop(k, None)
                st.rerun()
        else:
            st.info("Whitelist is empty. Check processes in the Flagged Anomalies tab and click Ignore.")

    st.divider()

    # ── LLM explanation ───────────────────────────────────────────────────────
    st.markdown('<p class="section-label">AI-powered threat analysis · powered by local Gemma 4B via Ollama</p>', unsafe_allow_html=True)
    if st.button("🤖 Explain Anomalies with Gemma 4B", use_container_width=True):
        with st.spinner("🧠 Querying local LLM — this may take up to 2 minutes..."):
            st.session_state["llm_response"] = get_llm_explanation(df_anomalies, df_all)

    if "llm_response" in st.session_state:
        st.subheader("🔍 LLM Security Analysis")
        st.info(st.session_state["llm_response"])


if __name__ == "__main__":
    main()
