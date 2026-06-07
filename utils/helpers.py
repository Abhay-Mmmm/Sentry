"""
Advanced security features and utility functions.
"""

from datetime import datetime
import pandas as pd
import streamlit as st

def calculate_health_score(df_all):
    """Calculate a system health score from 0 to 100."""
    if df_all is None or df_all.empty:
        return 0
    total = len(df_all)
    anomalies = len(df_all[df_all["Status"] == "Anomaly"])
    return max(0, round(100 - (anomalies / total * 100), 1))


def generate_export_report(reports):
    """Generate a markdown report from a list of report dictionaries."""
    md = "# Project Sentinel - Security Report\\n\\n"
    md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n"
    if not reports:
        md += "No reports available.\\n"
        return md
    for i, report in enumerate(reports, 1):
        md += f"## Report {i}\\n"
        md += f"- **Timestamp:** {report.get('Timestamp', 'N/A')}\\n"
        md += f"- **Threat Level:** {report.get('Threat Level', 'N/A')}\\n"
        md += f"- **Process Count:** {report.get('Process Count', 'N/A')}\\n"
        md += f"- **Summary:** {report.get('Summary', 'N/A')}\\n"
        md += f"\\n{report.get('Details', '')}\\n\\n---\\n"
    return md


def add_timeline_event(event_type, description, timestamp=None):
    """Add an event to the timeline in session state."""
    if "timeline_events" not in st.session_state:
        st.session_state["timeline_events"] = []
    st.session_state["timeline_events"].append({
        "timestamp": timestamp or datetime.now(),
        "type": event_type,
        "description": description,
    })

def get_health_gauge_value(health_score):
    """Return color for health gauge based on score."""
    if health_score > 80:
        return "#3FB950"
    elif health_score > 50:
        return "#D29922"
    else:
        return "#F85149"
