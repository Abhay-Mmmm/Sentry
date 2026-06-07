"""
Custom CSS Styles for Sentinel Dashboard
Professional dark cybersecurity theme
"""

import streamlit as st

def apply_custom_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"], .stMarkdown {
            font-family: 'Inter', sans-serif;
            background-color: #0D1117;
            color: #C9D1D9;
        }

        .main-header {
            font-size: 2rem;
            font-weight: 700;
            color: #58A6FF;
            margin-bottom: 0.5rem;
        }

        .sub-header {
            font-size: 1.1rem;
            font-weight: 400;
            color: #8B949E;
            margin-bottom: 2rem;
        }

        .metric-card {
            background-color: #161B22;
            border: 1px solid #30363D;
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.3s ease;
        }

        .metric-card:hover {
            border-color: #58A6FF;
            transform: translateY(-2px);
        }

        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            display: inline-block;
        }

        .status-normal {
            background-color: rgba(46, 160, 67, 0.15);
            color: #3FB950;
            border: 1px solid rgba(63, 185, 80, 0.3);
        }

        .status-warning {
            background-color: rgba(210, 153, 34, 0.15);
            color: #D29922;
            border: 1px solid rgba(210, 153, 34, 0.3);
        }

        .status-danger {
            background-color: rgba(248, 81, 73, 0.15);
            color: #F85149;
            border: 1px solid rgba(248, 81, 73, 0.3);
        }

        .stDataFrame {
            background-color: #161B22 !important;
            border: 1px solid #30363D !important;
            border-radius: 12px;
            overflow: hidden;
        }

        /* Accessibly styled highlighted table cells for dark mode compatibility */
        div[data-testid="stDataFrame"] td[style*="background-color: rgb(255, 224, 224)"],
        div[data-testid="stDataFrame"] td[style*="background-color: #ffe0e0"],
        div[data-testid="stTable"] td[style*="background-color: #ffe0e0"],
        table td[style*="background-color: #ffe0e0"] {
            color: #0D1117 !important;
            font-weight: 600 !important;
        }

        div[data-testid="stMetricValue"] {
            font-size: 2rem;
            font-weight: 700;
            color: #F0F6FC;
        }

        div[data-testid="stMetricDelta"] {
            font-size: 0.9rem;
        }

        .stButton > button {
            background-color: #21262D;
            color: #C9D1D9;
            border: 1px solid #30363D;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            transition: all 0.2s ease;
            width: 100%;
        }

        .stButton > button:hover {
            background-color: #30363D;
            border-color: #8B949E;
            color: #F0F6FC;
            transform: translateY(-1px);
        }

        /* Specific style for primary/accent buttons like scan and analyze */
        div[data-testid="stFormSubmitButton"] button,
        button[key*="analyze_btn"],
        button[key*="explain_gemma_btn"] {
            background-color: #238636 !important;
            color: white !important;
            border: none !important;
        }
        
        div[data-testid="stFormSubmitButton"] button:hover,
        button[key*="analyze_btn"]:hover,
        button[key*="explain_gemma_btn"]:hover {
            background-color: #2EA043 !important;
        }

        .stTextInput > div > div > input {
            background-color: #161B22;
            color: #C9D1D9;
            border: 1px solid #30363D;
            border-radius: 8px;
        }

        .stSelectbox > div > div > div {
            background-color: #161B22;
            color: #C9D1D9;
            border: 1px solid #30363D;
            border-radius: 8px;
        }

        .stSlider > div > div > div {
            color: #58A6FF;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3 {
            color: #F0F6FC;
        }

        .sidebar .sidebar-content {
            background-color: #161B22;
        }

        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #0D1117;
        }

        ::-webkit-scrollbar-thumb {
            background: #30363D;
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #484f58;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
