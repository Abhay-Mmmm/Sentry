"""
Sidebar Navigation for Sentinel Dashboard
Provides settings, mode switching, and scan control.
"""

import streamlit as st

def render_sidebar():
    with st.sidebar:
        # Title and Branding
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem;">
                <div style="font-size: 2rem;">🛡️</div>
                <div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #58A6FF; letter-spacing: 0.5px;">Sentinel OS</div>
                    <div style="font-size: 0.8rem; color: #8B949E; text-transform: uppercase; font-weight: 600;">AI Endpoint Security</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Dashboard Mode Selector
        st.markdown("### 🖥️ Dashboard Mode")
        mode = st.selectbox(
            "Select Interface Mode",
            ["📋 Sprint Contract View", "📊 Enterprise Security Dashboard"],
            index=0,
            key="dashboard_mode",
            label_visibility="collapsed"
        )

        st.markdown("---")

        page = "Dashboard Overview"
        # Navigation (Conditional on Mode)
        if mode == "📊 Enterprise Security Dashboard":
            st.markdown("### 🧭 Navigation")
            page = st.radio(
                "Navigation",
                [
                    "Dashboard Overview",
                    "Live Process Explorer",
                    "Anomaly Center",
                    "Threat Visualization",
                    "AI Security Analyst",
                    "Threat Inbox",
                    "Timeline View",
                ],
                label_visibility="collapsed",
                key="nav_page"
            )
            st.markdown("---")
        else:
            st.info("Operating under Sprint Contract constraints. Navigation is locked to the official monitor layout.")

        # Engine Control Settings
        st.markdown("### ⚙️ Engine Controls")
        
        # Manual Scan Trigger
        if st.button("🔄 Trigger System Rescan", use_container_width=True, help="Force refresh of telemetry and Isolation Forest run"):
            st.session_state["rescan_trigger"] = True
            st.success("Rescan queued!")
            st.rerun()

        # Auto Refresh Options
        auto_refresh = st.checkbox("Enable Auto Refresh", value=st.session_state.get("auto_refresh", False), key="auto_refresh_chk")
        st.session_state["auto_refresh"] = auto_refresh
        
        if auto_refresh:
            st.session_state["refresh_interval"] = st.slider(
                "Interval (seconds)",
                min_value=2,
                max_value=60,
                value=st.session_state.get("refresh_interval", 5),
                key="refresh_interval_slider"
            )

        # Ollama Model Configuration
        st.session_state["ollama_model"] = st.text_input(
            "Local LLM Model",
            value=st.session_state.get("ollama_model", "gemma"),
            help="Name of local Ollama model to use for explanations"
        )

        st.markdown("---")
        
        # System Health Status Indicator
        df_anomalies = st.session_state.get("df_anomalies")
        anom_count = len(df_anomalies) if df_anomalies is not None else 0
        if anom_count == 0:
            status_text = "🟢 System Healthy"
        elif anom_count < 10:
            status_text = "🟡 Warnings Active"
        else:
            status_text = "🔴 Critical Alerts"
            
        st.markdown(
            f"""
            <div style="background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 0.75rem; text-align: center;">
                <span style="font-weight: 600; color: #F0F6FC;">Status: {status_text}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.caption("Version: 1.1.0-Enterprise")
        st.caption("Team 1 | Sentinel Dashboard")

        return page
