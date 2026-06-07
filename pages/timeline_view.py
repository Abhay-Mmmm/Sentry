"""
Timeline View Page
Visualizes process start, anomaly detection, LLM analysis, and threat generation in a chronological stream.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def render_timeline_view():
    st.markdown("<div class='main-header'>Timeline View</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Chronological sequence of security events</div>", unsafe_allow_html=True)

    df_all = st.session_state.get("df_all")
    df_anomalies = st.session_state.get("df_anomalies")
    reports = st.session_state.get("threat_reports", [])
    manual_events = st.session_state.get("timeline_events", [])

    # Compile events from all sources
    events = []

    # 1. Process Start Events (from telemetry df_all)
    if df_all is not None and not df_all.empty and "Detection Time" in df_all.columns:
        # Take a subset to not overflow timeline (e.g. latest 30)
        for _, row in df_all.sort_values(by="Detection Time", ascending=False).head(30).iterrows():
            events.append({
                "Time": pd.to_datetime(row["Detection Time"]),
                "Event": f"Telemetry logged active process: `{row['Process']}` (PID: {row['PID']})",
                "Type": "Process Telemetry",
            })

    # 2. Anomaly Detections (from Team 2 df_anomalies)
    if df_anomalies is not None and not df_anomalies.empty and "Detection Time" in df_anomalies.columns:
        for _, row in df_anomalies.iterrows():
            events.append({
                "Time": pd.to_datetime(row["Detection Time"]),
                "Event": f"Isolation Forest flagged anomaly: `{row['Process']}` (Risk: {row['Risk Score']}/100, PID: {row['PID']})",
                "Type": "Anomaly Detection",
            })

    # 3. Report Generation Detections (from Team 3 reports)
    for report in reports:
        if "Timestamp" in report:
            events.append({
                "Time": pd.to_datetime(report["Timestamp"]),
                "Event": f"AI analyst security report generated. Severity: {report['Threat Level']}. {report['Summary']}",
                "Type": "Report Generation",
            })

    # 4. Manual Actions/Scans (from manual_events helper)
    for me in manual_events:
        t_val = me.get("timestamp")
        if isinstance(t_val, str):
            t_val = pd.to_datetime(t_val)
        events.append({
            "Time": pd.to_datetime(t_val),
            "Event": me.get("description", ""),
            "Type": me.get("type", "System Action"),
        })

    if not events:
        st.warning("No security events logged in current timeline. Run scans or trigger AI analysis to populate.")
        return

    # Sort events chronologically (newest at bottom for charts, but we will render list newest-first)
    df_events = pd.DataFrame(events).sort_values("Time").reset_index(drop=True)

    event_counts = df_events["Type"].value_counts().reset_index()
    event_counts.columns = ["Event Type", "Count"]

    col_chart, col_stat = st.columns([2, 1])
    
    with col_chart:
        st.markdown("#### Event Scatter Distribution")
        fig = px.scatter(
            df_events,
            x="Time",
            y="Type",
            color="Type",
            color_discrete_map={
                "Process Telemetry": "#58A6FF",
                "Anomaly Detection": "#F85149",
                "Report Generation": "#D29922",
                "Process Action": "#8B949E",
                "System Action": "#3FB950",
            },
            template="plotly_dark",
            hover_data=["Event"],
        )
        fig.update_traces(marker=dict(size=14, symbol="hexagon-open-dot", line=dict(width=1.5)))
        fig.update_layout(
            paper_bgcolor="#161B22", 
            plot_bgcolor="#0D1117",
            font_family="Inter, sans-serif",
            font_color="#C9D1D9",
            margin=dict(l=40, r=40, t=30, b=40),
            xaxis=dict(gridcolor="#30363D", title="Time Logged"),
            yaxis=dict(gridcolor="#30363D", title="Classification"),
            legend=dict(bgcolor="rgba(22, 27, 34, 0.8)", bordercolor="#30363D", borderwidth=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_stat:
        st.markdown("#### Event Classification")
        fig_pie = px.pie(
            event_counts,
            names="Event Type",
            values="Count",
            color="Event Type",
            color_discrete_map={
                "Process Telemetry": "#58A6FF",
                "Anomaly Detection": "#F85149",
                "Report Generation": "#D29922",
                "Process Action": "#8B949E",
                "System Action": "#3FB950",
            },
            template="plotly_dark",
            hole=0.45,
        )
        fig_pie.update_layout(
            paper_bgcolor="#161B22", 
            font_family="Inter, sans-serif",
            font_color="#C9D1D9",
            showlegend=True, 
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            margin=dict(l=20, r=20, t=30, b=20),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Chronological Incident & Activity Feed")
    st.caption("Incidents are sorted with the most recent actions at the top.")

    # Render vertical timeline in descending order (newest first)
    for idx, row in df_events.sort_values(by="Time", ascending=False).iterrows():
        etype = row["Type"]
        
        # Color matching
        color = "#58A6FF"  # Blue - Telemetry
        if etype == "Anomaly Detection":
            color = "#F85149"  # Red - Threat
        elif etype == "Report Generation":
            color = "#D29922"  # Yellow - AI
        elif etype == "System Action":
            color = "#3FB950"  # Green - Action
        elif etype == "Process Action":
            color = "#8B949E"  # Gray - Terminate/Isolate
            
        time_str = row['Time'].strftime('%Y-%m-%d %H:%M:%S')
        
        st.markdown(
            f"""
            <div style="position: relative; border-left: 2px solid #30363D; padding: 0.25rem 0 1.25rem 1.5rem; margin-left: 15px;">
                <div style="
                    position: absolute; 
                    left: -7px; 
                    top: 6px; 
                    width: 12px; 
                    height: 12px; 
                    border-radius: 50%; 
                    background-color: {color}; 
                    border: 2px solid #0D1117; 
                    box-shadow: 0 0 6px {color};
                "></div>
                <div style="color: #8B949E; font-size: 0.85rem; font-weight: 500; font-family: monospace;">{time_str}</div>
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 2px;">
                    <span style="color: #F0F6FC; font-weight: 700; font-size: 1rem;">{etype}</span>
                </div>
                <div style="color: #C9D1D9; font-size: 0.95rem; margin-top: 4px; line-height: 1.4;">
                    {row['Event']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
