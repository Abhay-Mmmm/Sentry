"""
Anomaly Center Page
Displays anomalous processes with risk-based color coding and interactive inline actions.
"""

import streamlit as st
import pandas as pd

def _get_risk_color(score):
    if score > 85:
        return "#F85149"  # Red - Critical
    elif score > 70:
        return "#FFA500"  # Orange - High
    elif score > 50:
        return "#D29922"  # Yellow - Medium
    else:
        return "#58A6FF"  # Blue - Informational

def _get_risk_label(score):
    if score > 85:
        return "Critical"
    elif score > 70:
        return "High"
    elif score > 50:
        return "Medium"
    else:
        return "Informational"

def render_anomaly_center(df_anomalies):
    st.markdown("<div class='main-header'>Anomaly Center</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Processes flagged by Team 2 for further investigation</div>", unsafe_allow_html=True)

    if df_anomalies is None or df_anomalies.empty:
        st.success("🛡️ No anomalies detected. System is operating normally.")
        return

    # Severity stats
    total_anomalies = len(df_anomalies)
    critical = len(df_anomalies[df_anomalies["Risk Score"] > 85])
    high = len(df_anomalies[(df_anomalies["Risk Score"] > 70) & (df_anomalies["Risk Score"] <= 85)])
    medium = len(df_anomalies[(df_anomalies["Risk Score"] > 50) & (df_anomalies["Risk Score"] <= 70)])
    info = len(df_anomalies[df_anomalies["Risk Score"] <= 50])

    cols = st.columns(4)
    with cols[0]:
        st.metric("Total Anomalies", total_anomalies)
    with cols[1]:
        st.metric("Critical Risks", critical, delta_color="inverse")
    with cols[2]:
        st.metric("High Risks", high)
    with cols[3]:
        st.metric("Medium & Info", medium + info)

    st.markdown("---")

    # Filters
    col1, col2 = st.columns([1, 2])
    with col1:
        min_risk = st.slider("Filter by Min Risk Score", 0, 100, 0, key="anomaly_risk_filter")
    with col2:
        name_filter = st.text_input("Filter by Process Name", placeholder="e.g., suspicious.exe", key="anomaly_name_filter")

    filtered = df_anomalies[df_anomalies["Risk Score"] >= min_risk]
    if name_filter:
        filtered = filtered[filtered["Process"].str.contains(name_filter, case=False, na=False)]

    st.markdown(f"**Displaying {len(filtered)} flagged anomalies**")

    # Interactive List of Anomaly Cards
    for idx, row in filtered.iterrows():
        risk_color = _get_risk_color(row["Risk Score"])
        risk_label = _get_risk_label(row["Risk Score"])
        
        # HTML card template
        card_html = f"""
        <div style="
            background-color: #161B22;
            border-left: 6px solid {risk_color};
            border-top: 1px solid #30363D;
            border-right: 1px solid #30363D;
            border-bottom: 1px solid #30363D;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.2rem; font-weight: 700; color: #F0F6FC;">{row['Process']}</span>
                    <span style="color: #8B949E; font-size: 0.9rem; margin-left: 0.5rem;">(PID: {row['PID']})</span>
                </div>
                <span style="
                    background-color: {risk_color}15;
                    color: {risk_color};
                    border: 1px solid {risk_color}30;
                    padding: 3px 12px;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    text-transform: uppercase;
                ">{risk_label}</span>
            </div>
            <div style="display: flex; gap: 2.5rem; margin-top: 1rem; color: #C9D1D9; font-size: 0.95rem;">
                <div>CPU Usage: <strong style="color: {risk_color};">{row['CPU (%)']}%</strong></div>
                <div>Memory: <strong>{row['Memory (%)']}%</strong></div>
                <div>Threads: <strong>{row['Threads']}</strong></div>
                <div>Risk Score: <strong style="color: {risk_color};">{row['Risk Score']}/100</strong></div>
                <div style="color: #8B949E;">Detection: {row['Detection Time'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['Detection Time'], 'strftime') else row['Detection Time']}</div>
            </div>
        </div>
        """
        
        col_card, col_action = st.columns([5.5, 1.2])
        with col_card:
            st.markdown(card_html, unsafe_allow_html=True)
        with col_action:
            # Inline interactive controls
            st.write("")  # padding to align buttons
            if st.button("🛡️ AI Explainer", key=f"explain_anom_{row['PID']}_{idx}", use_container_width=True):
                # Set a flag to navigate and trigger the explain request for this PID
                st.session_state["selected_anomaly_pid"] = row["PID"]
                st.session_state["dashboard_page"] = "AI Security Analyst"
                st.success(f"Dispatched PID {row['PID']} to AI analyst!")
                st.rerun()
                
            if st.button("🚫 Terminate", key=f"kill_anom_{row['PID']}_{idx}", use_container_width=True):
                # Simulate terminating process
                # Let's remove from session state
                st.session_state["base_df_all"] = st.session_state["base_df_all"][st.session_state["base_df_all"]["PID"] != row["PID"]]
                # Log timeline event
                from utils.helpers import add_timeline_event
                add_timeline_event("Process Action", f"Terminated anomalous process {row['Process']} (PID: {row['PID']})")
                st.warning(f"Process PID {row['PID']} ({row['Process']}) terminated!")
                st.rerun()

    # Data table for export
    st.markdown("---")
    st.markdown("#### Anomaly Telemetry Export")
    
    st.dataframe(
        filtered,
        column_config={
            "PID": st.column_config.NumberColumn("PID", format="%d"),
            "Process": st.column_config.TextColumn("Process Name"),
            "CPU (%)": st.column_config.ProgressColumn("CPU Usage", format="%.2f%%", min_value=0.0, max_value=100.0),
            "Memory (%)": st.column_config.ProgressColumn("Memory Usage", format="%.2f%%", min_value=0.0, max_value=100.0),
            "Threads": st.column_config.NumberColumn("Threads", format="%d"),
            "Status": st.column_config.TextColumn("Status"),
            "Risk Score": st.column_config.ProgressColumn("Risk Score", format="%d", min_value=0, max_value=100),
            "Detection Time": st.column_config.DatetimeColumn("Detection Time", format="YYYY-MM-DD HH:mm:ss")
        },
        use_container_width=True,
        hide_index=True
    )

    # CSV Export
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download CSV Report",
        data=csv,
        file_name="sentinel_anomalies.csv",
        mime="text/csv",
        use_container_width=True
    )
