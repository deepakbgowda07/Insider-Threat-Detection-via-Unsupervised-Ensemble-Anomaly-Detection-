# ============================================================================
# STYLING & UI MODULE
# ============================================================================

import streamlit as st


def apply_theme():
    """Apply dark theme styling to dashboard"""
    st.markdown(
        """
        <style>
        body {
            background-color: #0a0e27;
            color: #e0e0e0;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 2px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: #1a1f3a;
            border-radius: 4px 4px 0 0;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #2a4f7f;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #1a1f3a, #141829);
            border: 1px solid #2a2f4a;
            border-radius: 8px;
            padding: 16px;
        }
        
        .risk-critical { color: #ff4444; font-weight: bold; }
        .risk-high { color: #ff9800; font-weight: bold; }
        .risk-medium { color: #fbc02d; font-weight: bold; }
        .risk-normal { color: #66bb6a; }
        
        .section-header {
            border-bottom: 2px solid #2a4f7f;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def set_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="Insider Threat Detection | SOC Dashboard",
        layout="wide",
        initial_sidebar_state="expanded"
    )
