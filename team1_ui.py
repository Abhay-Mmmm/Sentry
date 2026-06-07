"""
Team 1 — UI & Engine
File during sprint: team1_ui.py
"""

import streamlit as st
import pandas as pd
from mock.team3_interface import get_llm_explanation

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
    st.title("Project Sentinel — Local Anomaly Monitor")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Processes", len(df_all))
    col2.metric("Anomalies Detected", len(df_anomalies))
    rate = (len(df_anomalies) / len(df_all) * 100) if len(df_all) > 0 else 0.0
    col3.metric("Anomaly Rate", f"{rate:.1f}%")

    st.subheader("All Process Telemetry")
    # Ensure is_anomaly column exists to prevent style key error
    if "is_anomaly" not in df_all.columns:
        if "Status" in df_all.columns:
            df_all["is_anomaly"] = df_all["Status"] == "Anomaly"
        else:
            df_all["is_anomaly"] = False

    styled_df = df_all.style.apply(
        lambda row: ['background-color: #ffe0e0' if row['is_anomaly'] else '' for _ in row],
        axis=1
    )
    st.dataframe(styled_df, use_container_width=True)

    st.subheader("Flagged Anomalies")
    st.dataframe(df_anomalies, use_container_width=True)

    if st.button("Explain Anomalies with Gemma 2B"):
        with st.spinner("Querying local LLM..."):
            explanation = get_llm_explanation(df_anomalies)
            st.session_state["llm_response"] = explanation

    if "llm_response" in st.session_state:
        st.subheader("LLM Security Analysis")
        st.info(st.session_state["llm_response"])
