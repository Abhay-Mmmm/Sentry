"""
Sentinel Dashboard - Main Application Entrypoint
Team 1 - Frontend & UI/UX
"""

import streamlit as st
import warnings
warnings.filterwarnings("ignore")

# Initialize session state first to ensure settings are present
from utils.session_state import initialize_session_state
initialize_session_state()

from components.sidebar import render_sidebar
from components.styles import apply_custom_styles
from pages.overview import render_overview
from pages.process_explorer import render_process_explorer
from pages.anomaly_center import render_anomaly_center
from pages.threat_visualization import render_threat_visualization
from pages.ai_analyst import render_ai_analyst
from pages.threat_inbox import render_threat_inbox
from pages.timeline_view import render_timeline_view
from mock.team2_interface import get_anomalies
import team1_ui

def main():
    st.set_page_config(
        page_title="Sentinel | AI Security Analyst",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    apply_custom_styles()

    # Fetch data from Team 2 (with fallback & dynamic drift)
    df_all, df_anomalies = get_anomalies()
    st.session_state["df_all"] = df_all
    st.session_state["df_anomalies"] = df_anomalies

    # Render Sidebar and get mode/page
    page_selected = render_sidebar()
    mode = st.session_state.get("dashboard_mode", "📋 Sprint Contract View")

    # Handle page routing
    if mode == "📋 Sprint Contract View":
        # Call Team 1 Sprint Contract Dashboard
        team1_ui.render_dashboard(df_all, df_anomalies)
    else:
        # Enterprise Mode Multi-page Routing
        page = page_selected
        
        # Priority for overrides (e.g. from Anomaly Center list button clicks)
        if "dashboard_page" in st.session_state:
            st.session_state["nav_page"] = st.session_state["dashboard_page"]
            del st.session_state["dashboard_page"]
            st.rerun()

        # Render corresponding pages
        if page == "Dashboard Overview":
            render_overview(df_all, df_anomalies)
        elif page == "Live Process Explorer":
            render_process_explorer(df_all)
        elif page == "Anomaly Center":
            render_anomaly_center(df_anomalies)
        elif page == "Threat Visualization":
            render_threat_visualization(df_all, df_anomalies)
        elif page == "AI Security Analyst":
            render_ai_analyst(df_anomalies)
        elif page == "Threat Inbox":
            render_threat_inbox()
        elif page == "Timeline View":
            render_timeline_view()

    # Auto Refresh Logic (executed at the end of the run)
    if st.session_state.get("auto_refresh", False):
        import time
        interval = st.session_state.get("refresh_interval", 5)
        time.sleep(interval)
        st.rerun()

if __name__ == "__main__":
    main()
