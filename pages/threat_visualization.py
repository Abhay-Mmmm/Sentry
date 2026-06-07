"""
Threat Visualization Page
Interactive Plotly charts for threat and resource analysis.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

def render_threat_visualization(df_all, df_anomalies):
    st.markdown("<div class='main-header'>Threat Visualization</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Interactive charts and resource distribution analysis</div>", unsafe_allow_html=True)

    if df_all is None or df_all.empty:
        st.warning("No process data available for visualization.")
        return

    tab1, tab2, tab3 = st.tabs(["🎯 Threat Scatter Plot", "📊 Resource Distributions", "🔥 Heatmaps & Over-Time Trends"])

    # --- Tab 1: Scatter Plot ---
    with tab1:
        st.markdown("#### Threat Analysis Scatter Plot (CPU vs Memory)")
        st.caption("Point size is scaled by Process Risk Score. Anomalous processes are colored red.")

        df_plot = df_all.copy()
        # Scale sizes: normal is smaller, anomalies are scaled by risk
        df_plot["Point Size"] = np.where(
            df_plot["Status"] == "Anomaly", 
            df_plot["Risk Score"] * 0.4 + 10, 
            5
        )

        fig = px.scatter(
            df_plot,
            x="CPU (%)",
            y="Memory (%)",
            color="Status",
            color_discrete_map={"Normal": "#3FB950", "Anomaly": "#F85149"},
            size="Point Size",
            hover_data=["Process", "PID", "Threads", "Risk Score"],
            template="plotly_dark",
            size_max=25,
        )
        
        fig.update_layout(
            paper_bgcolor="#161B22", 
            plot_bgcolor="#0D1117",
            font_family="Inter, sans-serif",
            font_color="#C9D1D9",
            margin=dict(l=40, r=40, t=20, b=40),
            xaxis=dict(gridcolor="#30363D", title="CPU Usage (%)"),
            yaxis=dict(gridcolor="#30363D", title="Memory Usage (%)"),
            legend=dict(bgcolor="rgba(22, 27, 34, 0.8)", bordercolor="#30363D", borderwidth=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Tab 2: Resource Distributions ---
    with tab2:
        col1, col2, col3 = st.columns(3)
        charts = [
            ("CPU Distribution", "CPU (%)", col1, "#58A6FF"),
            ("Memory Distribution", "Memory (%)", col2, "#D29922"),
            ("Thread Count Distribution", "Threads", col3, "#3FB950"),
        ]
        for title, col, container, color in charts:
            with container:
                st.markdown(f"##### {title}")
                fig = px.histogram(
                    df_all, 
                    x=col, 
                    nbins=25, 
                    color="Status",
                    color_discrete_map={"Normal": color, "Anomaly": "#F85149"},
                    template="plotly_dark"
                )
                fig.update_layout(
                    paper_bgcolor="#161B22", 
                    plot_bgcolor="#0D1117",
                    font_family="Inter, sans-serif",
                    font_color="#C9D1D9",
                    showlegend=True,
                    xaxis=dict(gridcolor="#30363D"),
                    yaxis=dict(gridcolor="#30363D"),
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)

    # --- Tab 3: Heatmap & Trends ---
    with tab3:
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("#### Resource Concentration Heatmap")
            st.caption("Binned CPU vs Memory density indicating cluster zones.")
            
            # Form clean bins
            df_hm = df_all.copy()
            df_hm["CPU Bin"] = pd.cut(df_hm["CPU (%)"], bins=8, labels=[f"{int(x.left)}-{int(x.right)}%" for x in pd.cut(df_hm["CPU (%)"], bins=8).unique().sort_values()])
            df_hm["Mem Bin"] = pd.cut(df_hm["Memory (%)"], bins=8, labels=[f"{int(x.left)}-{int(x.right)}%" for x in pd.cut(df_hm["Memory (%)"], bins=8).unique().sort_values()])
            
            pivot = df_hm.pivot_table(index="CPU Bin", columns="Mem Bin", values="PID", aggfunc="count", fill_value=0)
            
            fig_hm = px.imshow(
                pivot,
                text_auto=True,
                color_continuous_scale="Viridis",
                template="plotly_dark",
                aspect="auto",
            )
            fig_hm.update_layout(
                paper_bgcolor="#161B22",
                plot_bgcolor="#0D1117",
                xaxis=dict(title="Memory Bin (%)", color="#C9D1D9", tickangle=45),
                yaxis=dict(title="CPU Bin (%)", color="#C9D1D9"),
                margin=dict(l=40, r=40, t=30, b=40),
            )
            st.plotly_chart(fig_hm, use_container_width=True)
            
        with col_right:
            st.markdown("#### Threat Trends Over Time")
            st.caption("Hourly aggregation of anomalous process detections.")
            
            if "Detection Time" in df_all.columns:
                df_time = df_all.copy()
                df_time["Hour"] = pd.to_datetime(df_time["Detection Time"]).dt.floor("H")
                # Group and fill missing hours
                counts = df_time[df_time["Status"] == "Anomaly"].groupby("Hour").size().reset_index(name="Anomaly Count")
                
                if not counts.empty:
                    fig_line = px.area(
                        counts, 
                        x="Hour", 
                        y="Anomaly Count", 
                        template="plotly_dark"
                    )
                    fig_line.update_traces(
                        line=dict(color="#F85149", width=2),
                        fillcolor="rgba(248, 81, 73, 0.15)"
                    )
                    fig_line.update_layout(
                        paper_bgcolor="#161B22", 
                        plot_bgcolor="#0D1117",
                        font_color="#C9D1D9",
                        xaxis=dict(gridcolor="#30363D", title="Time"),
                        yaxis=dict(gridcolor="#30363D", title="Anomaly Count"),
                        margin=dict(l=40, r=40, t=30, b=40)
                    )
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("No time-series anomaly data available. Monitor systems to log historical metrics.")
            else:
                st.info("Telemetry lacks timestamps required for historical trends.")
