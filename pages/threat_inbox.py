"""
Threat Inbox Page
Stores, displays, and manages generated security reports.
"""

import streamlit as st
import pandas as pd

def render_threat_inbox():
    st.markdown("<div class='main-header'>Threat Inbox</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Manage and review AI-generated security reports</div>", unsafe_allow_html=True)

    reports = st.session_state.get("threat_reports", [])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reports", len(reports))
    with col2:
        critical = sum(1 for r in reports if r.get("Threat Level") == "Critical")
        st.metric("Critical Reports", critical, delta_color="inverse")
    with col3:
        if st.button("🗑️ Clear All Reports", key="clear_inbox_btn", use_container_width=True):
            st.session_state["threat_reports"] = []
            st.success("All reports cleared.")
            st.rerun()

    st.markdown("---")

    if not reports:
        st.info("No reports in the inbox. Visit the AI Security Analyst page to generate reports.")
        return

    search = st.text_input("Search reports by process or threat level", placeholder="e.g., Critical, chrome.exe", key="inbox_search")

    # Render reports in reverse chronological order (newest first)
    for idx, report in enumerate(reversed(reports)):
        # Calculate original index in reports list
        original_idx = len(reports) - 1 - idx
        
        # Search filter check
        if search:
            search_lower = search.lower()
            match_summary = search_lower in report.get("Summary", "").lower()
            match_level = search_lower in report.get("Threat Level", "").lower()
            match_details = search_lower in report.get("Details", "").lower()
            if not (match_summary or match_level or match_details):
                continue

        threat_level = report.get("Threat Level", "Medium")
        severity_class = (
            "status-danger" if threat_level == "Critical"
            else "status-warning" if threat_level == "High"
            else "status-normal"
        )
        status_color = "#F85149" if threat_level == "Critical" else "#FFA500" if threat_level == "High" else "#58A6FF"

        with st.container():
            st.markdown(
                f"""
                <div style="
                    background-color: #161B22; 
                    border: 1px solid #30363D; 
                    border-left: 5px solid {status_color};
                    border-radius: 8px; 
                    padding: 1.25rem; 
                    margin-bottom: 0.5rem;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #F0F6FC; font-size: 1.15rem;">Security Analysis Report</strong>
                            <span style="color: #8B949E; margin-left: 1rem; font-size: 0.9rem;">{report['Timestamp']}</span>
                        </div>
                        <span class="status-badge {severity_class}">{threat_level.upper()}</span>
                    </div>
                    <div style="margin-top: 0.75rem; color: #C9D1D9; font-size: 0.95rem; line-height: 1.4;">
                        <strong>Telemetry Scope:</strong> {report.get('Process Count', 0)} Anomalies Flagged<br>
                        <strong>Executive Summary:</strong> {report.get('Summary', '')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Details expander
            with st.expander("🔍 View Full AI Analyst Report Details", expanded=False):
                st.markdown(report.get("Details", "No details available."))
                
                # Download single report
                st.download_button(
                    label=f"📥 Download Report {report['Timestamp']} (.md)",
                    data=report.get("Details", ""),
                    file_name=f"sentinel_report_{report['Timestamp'].replace(' ', '_').replace(':', '-')}.md",
                    mime="text/markdown",
                    key=f"download_single_{original_idx}"
                )

            # Dismiss button next to report
            col_del, col_pad = st.columns([1, 4])
            with col_del:
                if st.button("Dismiss Alert", key=f"dismiss_{original_idx}", use_container_width=True):
                    # Remove from threat reports list
                    reports.pop(original_idx)
                    st.session_state["threat_reports"] = reports
                    st.success("Alert dismissed.")
                    st.rerun()
            st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Export All Inbox Metadata")
    
    if reports:
        # Create metadata dataframe for export (strip full markdown details to keep CSV lightweight)
        csv_data = pd.DataFrame(reports)
        csv_data = csv_data.drop(columns=["Details"], errors="ignore")
        csv_bytes = csv_data.to_csv(index=False).encode("utf-8")
        
        st.download_button(
            label="📥 Download All Reports Summary (CSV)",
            data=csv_bytes,
            file_name="sentinel_reports_inbox.csv",
            mime="text/csv",
            use_container_width=True
        )
