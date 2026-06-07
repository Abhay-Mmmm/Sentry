"""
AI Security Analyst Page
Allows triggering LLM analysis on anomalies and displays the generated report.
"""

import streamlit as st
import pandas as pd
from mock.team3_interface import generate_security_report

def render_ai_analyst(df_anomalies):
    st.markdown("<div class='main-header'>AI Security Analyst</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Leverage AI to analyze anomalies and generate security reports</div>", unsafe_allow_html=True)

    if df_anomalies is None or df_anomalies.empty:
        st.success("🛡️ No anomalies detected. AI analyst reports that endpoint is currently clean.")
        return

    # Focused PID check (if navigated from Anomaly Center)
    selected_pid = st.session_state.get("selected_anomaly_pid", None)
    
    df_to_analyze = df_anomalies.copy()
    if selected_pid is not None:
        df_to_analyze = df_anomalies[df_anomalies["PID"] == selected_pid]
        if df_to_analyze.empty:
            st.warning(f"PID {selected_pid} is no longer active. Analyzing all active anomalies instead.")
            df_to_analyze = df_anomalies
            st.session_state["selected_anomaly_pid"] = None
        else:
            st.info(f"🎯 **Focused Mode:** AI will target explanation for process `{df_to_analyze.iloc[0]['Process']}` (PID: {selected_pid}).")
            if st.button("Clear Focus (Show All)", key="clear_pid_focus"):
                st.session_state["selected_anomaly_pid"] = None
                st.rerun()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Processes to Analyze", len(df_to_analyze))
    with col2:
        st.metric("Reports in Inbox", len(st.session_state.get("threat_reports", [])))
    with col3:
        status_lbl = "Analyzing..." if st.session_state.get("analyzing", False) else "Idle"
        st.metric("Analyst Status", status_lbl)

    st.markdown("---")

    st.markdown("#### Anomalies Pending Analysis")
    st.dataframe(
        df_to_analyze[['Process', 'PID', 'CPU (%)', 'Memory (%)', 'Risk Score', 'Threads']].reset_index(drop=True), 
        use_container_width=True
    )

    st.markdown("---")

    col_btn1, col_btn2 = st.columns([1, 1])

    with col_btn1:
        btn_label = "🛡️ Run Targeted AI Analysis" if selected_pid else "🛡️ Analyze All Threats"
        if st.button(btn_label, key="analyze_btn", use_container_width=True, help="Send telemetry anomalies to Team 3 Gemma LLM"):
            st.session_state["analyzing"] = True
            with st.spinner("Consulting AI Security Analyst (Ollama/Gemma)..."):
                try:
                    report = generate_security_report(df_to_analyze)
                    st.session_state["last_report"] = report
                    
                    # Store in Threat Inbox
                    highest_risk = df_to_analyze["Risk Score"].max()
                    threat_level = "Critical" if highest_risk > 85 else "High" if highest_risk > 70 else "Medium"
                    proc_names = df_to_analyze["Process"].tolist()
                    summary_text = f"Analyzed {len(df_to_analyze)} processes (Top: {proc_names[0]})."
                    
                    reports_copy = list(st.session_state.get("threat_reports", []))
                    reports_copy.append({
                        "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Threat Level": threat_level,
                        "Process Count": len(df_to_analyze),
                        "Summary": summary_text,
                        "Details": report,
                    })
                    st.session_state["threat_reports"] = reports_copy
                    
                    # Add event to timeline
                    from utils.helpers import add_timeline_event
                    add_timeline_event("Report Generation", f"AI generated security report ({threat_level} risk level)")
                    
                    st.session_state["analyzing"] = False
                    st.success("Analysis complete! Report saved to Threat Inbox.")
                    st.rerun()
                except Exception as e:
                    st.session_state["analyzing"] = False
                    st.error(f"Analysis failed: {str(e)}")

    with col_btn2:
        if st.button("↻ Clear Report Preview", key="clear_preview_btn", use_container_width=True):
            if "last_report" in st.session_state:
                del st.session_state["last_report"]
                st.rerun()

    # Display Report Preview if it exists
    if "last_report" in st.session_state:
        st.markdown("---")
        st.markdown("### 📋 Security Analysis Report Preview")
        
        # Display nicely in styled container
        st.markdown(
            f"""
            <div style="background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem;">
                {st.markdown(st.session_state["last_report"])}
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Action Buttons
        col_down1, col_down2 = st.columns(2)
        with col_down1:
            st.download_button(
                label="📥 Download Report (.md)",
                data=st.session_state["last_report"],
                file_name="sentinel_ai_report.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col_down2:
            csv_bytes = df_to_analyze.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📊 Download Telemetry (CSV)",
                data=csv_bytes,
                file_name="analyzed_telemetry.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.markdown("---")
        st.info("Click the 'Analyze' button to query the AI Security Analyst and view the report here.")
