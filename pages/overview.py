"""
Dashboard Overview Page
Displays high-level metrics and status indicators.
"""

import streamlit as st
import plotly.graph_objects as go


COLOR_SAFE = "#3FB950"
COLOR_WARN = "#D29922"
COLOR_DANGER = "#F85149"
COLOR_INFO = "#58A6FF"


def render_header(title: str, subtitle: str):
    st.markdown(f"<div class='main-header'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-header'>{subtitle}</div>", unsafe_allow_html=True)


def _get_kpi_values(df_all, df_anomalies):
    total = len(df_all)
    anomalies = len(df_anomalies)
    avg_cpu = round(df_all["CPU (%)"].mean(), 2) if total > 0 else 0.0
    avg_mem = round(df_all["Memory (%)"].mean(), 2) if total > 0 else 0.0
    return total, anomalies, avg_cpu, avg_mem


def _top_consumers(df, col, top_n=5):
    return df.sort_values(by=col, ascending=False).head(top_n)["Process"].tolist()


def render_overview(df_all, df_anomalies):
    render_header("Dashboard Overview", "Real-time system health and anomaly summary")
    if df_all is None or df_all.empty:
        st.warning("No process data available.")
        return

    total, anomalies, avg_cpu, avg_mem = _get_kpi_values(df_all, df_anomalies)
    threat_status = "Critical" if anomalies > 20 else "Warning" if anomalies > 5 else "Normal"
    health_color = COLOR_DANGER if threat_status == "Critical" else COLOR_WARN if threat_status == "Warning" else COLOR_SAFE
    anomaly_pct = round((anomalies / total) * 100, 1) if total > 0 else 0

    # KPI Cards
    cols = st.columns(5)
    with cols[0]:
        st.metric("Total Processes", total, f"{total - anomalies} normal")
    with cols[1]:
        st.metric("Active Anomalies", anomalies, f"{anomaly_pct}% of total", delta_color="inverse")
    with cols[2]:
        st.metric("Avg CPU Usage", f"{avg_cpu}%", "System load")
    with cols[3]:
        st.metric("Avg Memory Usage", f"{avg_mem}%", "System load")
    with cols[4]:
        st.metric("Threat Status", threat_status, "", delta_color="inverse")

    st.markdown("---")

    # System Health & Severity
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.markdown("#### System Health")
        health = max(0, min(100, 100 - (anomalies / max(total, 1) * 100)))
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(health, 1),
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100], 'tickcolor': '#C9D1D9'},
                'bar': {'color': COLOR_SAFE if health > 80 else COLOR_WARN if health > 50 else COLOR_DANGER},
                'bgcolor': '#161B22',
                'bordercolor': '#30363D',
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(248,81,73,0.15)'},
                    {'range': [50, 80], 'color': 'rgba(210,153,34,0.15)'},
                    {'range': [80, 100], 'color': 'rgba(46,160,67,0.15)'}
                ]
            }
        ))
        fig.update_layout(paper_bgcolor='#0D1117', font_color='#C9D1D9', margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Anomaly Trend")
        # Simple trend chart (generated)
        import pandas as pd
        import numpy as np
        trend_data = pd.DataFrame({
            "Time": pd.date_range(end=pd.Timestamp.now(), periods=20, freq="5min"),
            "Anomalies": np.random.poisson(max(1, anomalies // 5), 20)
        })
        fig_trend = go.Figure(go.Scatter(
            x=trend_data["Time"], y=trend_data["Anomalies"], mode='lines+markers',
            line=dict(color=COLOR_INFO), marker=dict(size=6), fill='tozeroy', fillcolor='rgba(88,166,255,0.1)'
        ))
        fig_trend.update_layout(paper_bgcolor='#0D1117', plot_bgcolor='#0D1117', font_color='#C9D1D9',
                                  margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_trend, use_container_width=True)

    with col3:
        st.markdown("#### Severity Breakdown")
        severity_labels = ['Critical', 'High', 'Medium', 'Low']
        severity_counts = [
            len(df_anomalies[df_anomalies['Risk Score'] > 85]) if df_anomalies is not None else 0,
            len(df_anomalies[(df_anomalies['Risk Score'] > 70) & (df_anomalies['Risk Score'] <= 85)]) if df_anomalies is not None else 0,
            len(df_anomalies[(df_anomalies['Risk Score'] > 50) & (df_anomalies['Risk Score'] <= 70)]) if df_anomalies is not None else 0,
            len(df_anomalies[df_anomalies['Risk Score'] <= 50]) if df_anomalies is not None else 0,
        ]
        if sum(severity_counts) == 0:
            severity_counts = [0, 0, 0, 1]  # Prevent empty pie chart crash
        fig_pie = go.Figure(data=[go.Pie(labels=severity_labels, values=severity_counts, hole=.4,
                                            marker_colors=[COLOR_DANGER, COLOR_WARN, '#D29922', COLOR_INFO])])
        fig_pie.update_layout(paper_bgcolor='#0D1117', font_color='#C9D1D9',
                              showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.1),
                              margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    # Top Consumers & Recent Threats
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Top CPU Consumers")
        if df_anomalies is not None and not df_anomalies.empty:
            top_cpu = df_anomalies.nlargest(5, 'CPU (%)')[['Process', 'CPU (%)', 'Risk Score']].reset_index(drop=True)
            top_cpu.index = top_cpu.index + 1
            st.dataframe(top_cpu, use_container_width=True)
        else:
            st.info("No anomaly data available.")

    with col2:
        st.markdown("#### Recent Anomalies")
        if df_anomalies is not None and not df_anomalies.empty:
            recent = df_anomalies.sort_values(by='Detection Time', ascending=False).head(5)[['Process', 'Risk Score', 'Detection Time']].reset_index(drop=True)
            recent.index = recent.index + 1
            st.dataframe(recent, use_container_width=True)
        else:
            st.info("No anomalies detected recently.")

    # Threat Feed
    st.markdown("---")
    st.markdown("#### Recent Threat Feed")
    if df_anomalies is not None and not df_anomalies.empty:
        for _, row in df_anomalies.head(5).iterrows():
            severity_class = "status-danger" if row['Risk Score'] > 85 else "status-warning" if row['Risk Score'] > 60 else "status-normal"
            severity_text = "Critical" if row['Risk Score'] > 85 else "High" if row['Risk Score'] > 60 else "Medium"
            st.markdown(
                f"""
                <div style="background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: #F0F6FC;">{row['Process']}</strong> <span>(PID: {row['PID']})</span>
                        <div style="color: #8B949E; font-size: 0.85rem;">CPU: {row['CPU (%)']}% | Memory: {row['Memory (%)']}% | Threads: {row['Threads']}</div>
                    </div>
                    <div>
                        <span class="status-badge {severity_class}">{severity_text}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("All clear. No threats in the feed.")
