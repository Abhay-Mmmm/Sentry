"""
Live Process Explorer Page
Interactive table with search, sort, and filter capabilities.
"""

import streamlit as st
import pandas as pd

def render_process_explorer(df_all):
    st.markdown("<div class='main-header'>Live Process Explorer</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Monitor and filter running processes</div>", unsafe_allow_html=True)

    if df_all is None or df_all.empty:
        st.warning("No process data available.")
        return

    # Advanced Filters
    col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1])
    with col1:
        search = st.text_input("Search by Process Name or PID", placeholder="e.g., chrome.exe or 12345", key="proc_search")
    with col2:
        status_filter = st.selectbox("Status Filter", ["All", "Normal", "Anomaly"], key="proc_status")
    with col3:
        min_cpu = st.number_input("Min CPU %", min_value=0.0, max_value=100.0, value=0.0, step=5.0)
    with col4:
        sort_by = st.selectbox("Sort By", ["PID", "Process", "CPU (%)", "Memory (%)", "Threads", "Risk Score"], index=1, key="proc_sort")

    # Filter operations
    filtered = df_all.copy()
    
    if search:
        filtered = filtered[
            filtered["Process"].str.contains(search, case=False, na=False) |
            filtered["PID"].astype(str).str.contains(search, na=False)
        ]
        
    if status_filter != "All":
        filtered = filtered[filtered["Status"] == status_filter]
        
    if min_cpu > 0:
        filtered = filtered[filtered["CPU (%)"] >= min_cpu]

    # Sort operations
    if sort_by:
        # Default risk score to descending because security analysts care about highest risk first
        ascending = sort_by not in ["Risk Score", "CPU (%)", "Memory (%)"]
        filtered = filtered.sort_values(by=sort_by, ascending=ascending)

    st.markdown(f"**Showing {len(filtered)} active processes**")
    
    # Premium Column configuration for Streamlit dataframe
    st.dataframe(
        filtered,
        column_config={
            "PID": st.column_config.NumberColumn("PID", format="%d"),
            "Process": st.column_config.TextColumn("Process Name"),
            "CPU (%)": st.column_config.ProgressColumn("CPU Usage", format="%.2f%%", min_value=0.0, max_value=100.0),
            "Memory (%)": st.column_config.ProgressColumn("Memory Usage", format="%.2f%%", min_value=0.0, max_value=100.0),
            "Threads": st.column_config.NumberColumn("Threads", format="%d"),
            "Status": st.column_config.TextColumn("Status"),
            "is_anomaly": st.column_config.CheckboxColumn("Anomaly?"),
            "Risk Score": st.column_config.ProgressColumn("Risk Score", format="%d", min_value=0, max_value=100),
            "Detection Time": st.column_config.DatetimeColumn("Detection Time", format="YYYY-MM-DD HH:mm:ss")
        },
        use_container_width=True,
        height=600,
        hide_index=True
    )
