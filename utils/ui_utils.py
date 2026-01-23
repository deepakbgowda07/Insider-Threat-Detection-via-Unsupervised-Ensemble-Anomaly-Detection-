# ============================================================================
# UI UTILITIES MODULE
# ============================================================================

import streamlit as st
import pandas as pd
from datetime import datetime


def risk_to_color(risk_level):
    """
    Convert risk level to color code
    
    Args:
        risk_level (float or str): Risk score between 0 and 1, or risk level string
        
    Returns:
        str: Hex color code
    """
    # Handle string risk levels
    if isinstance(risk_level, str):
        if "CRITICAL" in risk_level:
            return "#ff4444"  # Critical - Red
        elif "HIGH" in risk_level:
            return "#ff9800"  # High - Orange
        elif "MEDIUM" in risk_level:
            return "#fbc02d"  # Medium - Yellow
        else:
            return "#66bb6a"  # Normal - Green
    
    # Handle numeric scores
    if risk_level >= 0.8:
        return "#ff4444"  # Critical - Red
    elif risk_level >= 0.6:
        return "#ff9800"  # High - Orange
    elif risk_level >= 0.4:
        return "#fbc02d"  # Medium - Yellow
    else:
        return "#66bb6a"  # Normal - Green


def get_risk_description(risk_level):
    """
    Get risk level description
    
    Args:
        risk_level (float): Risk score between 0 and 1
        
    Returns:
        str: Risk level description
    """
    if risk_level >= 0.8:
        return "🔴 CRITICAL"
    elif risk_level >= 0.6:
        return "🟠 HIGH"
    elif risk_level >= 0.4:
        return "🟡 MEDIUM"
    else:
        return "🟢 NORMAL"


def render_risk_summary_bar(df_input):
    """
    Render a horizontal bar showing risk distribution
    
    Args:
        df_input (pd.DataFrame): DataFrame with 'Ensemble_Score' column
    """
    col1, col2, col3, col4, col5 = st.columns([0.5, 0.25, 0.25, 0.25, 0.25])
    
    with col1:
        st.markdown("**Risk Distribution:**")
    
    total = len(df_input)
    critical = len(df_input[df_input['ensemble_score'] >= 0.8])
    high = len(df_input[(df_input['ensemble_score'] >= 0.6) & (df_input['ensemble_score'] < 0.8)])
    medium = len(df_input[(df_input['ensemble_score'] >= 0.4) & (df_input['ensemble_score'] < 0.6)])
    normal = len(df_input[df_input['ensemble_score'] < 0.4])
    
    with col2:
        st.markdown(f"<span style='color: #ff4444; font-weight: bold;'>🔴 CRITICAL: {critical}</span>", 
                   unsafe_allow_html=True)
    with col3:
        st.markdown(f"<span style='color: #ff9800; font-weight: bold;'>🟠 HIGH: {high}</span>", 
                   unsafe_allow_html=True)
    with col4:
        st.markdown(f"<span style='color: #fbc02d; font-weight: bold;'>🟡 MEDIUM: {medium}</span>", 
                   unsafe_allow_html=True)
    with col5:
        st.markdown(f"<span style='color: #66bb6a;'>🟢 NORMAL: {normal}</span>", 
                   unsafe_allow_html=True)


def render_header(title, icon="📊"):
    """
    Render a section header
    
    Args:
        title (str): Header title
        icon (str): Icon emoji
    """
    st.markdown(f"## {icon} {title}")
    st.divider()
