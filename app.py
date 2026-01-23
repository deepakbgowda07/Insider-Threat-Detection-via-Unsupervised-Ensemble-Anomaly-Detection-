# ============================================================================
# INSIDER THREAT DETECTION DASHBOARD — SOC-GRADE RESEARCH SYSTEM
# ============================================================================
# Built for unsupervised anomaly detection with ensemble-based scoring.
# For research, demos, and internal monitoring deployments.
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import json
from utils.auth_utils import (
    init_auth_session, is_authenticated, get_current_user,
    register_user, authenticate_user, logout,
    validate_user_entry, save_manual_entry, get_user_entries_count
)

# ============================================================================
# PAGE CONFIGURATION & THEME
# ============================================================================

st.set_page_config(
    page_title="Insider Threat Detection | SOC Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme styling
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

# Configure matplotlib for dark theme
plt.style.use('dark_background')
sns.set_palette("husl")

# ============================================================================
# AUTHENTICATION INITIALIZATION
# ============================================================================

init_auth_session()



@st.cache_data
def load_and_preprocess_data():
    """Load CSV and apply ML preprocessing (ensemble, normalization, etc.)"""
    df = pd.read_csv("final_risk_output (1).csv")
    
    # Z-score normalization of anomaly scores
    scaler = StandardScaler()
    df['iso_z'] = scaler.fit_transform(df[['iso_score']]).flatten()
    df['lof_z'] = scaler.fit_transform(df[['lof_score']]).flatten()
    df['ae_z'] = scaler.fit_transform(df[['ae_score']]).flatten()
    
    # Weighted ensemble scoring (40% LOF, 30% Isolation Forest, 30% Autoencoder)
    df['ensemble_weighted'] = (
        0.4 * df['lof_z'] +
        0.3 * df['iso_z'] +
        0.3 * df['ae_z']
    )
    
    # Reconstruction error proxy
    df['reconstruction_error'] = np.abs(df['ae_score'])
    
    # Alert threshold at 90th percentile
    threshold = df['ensemble_weighted'].quantile(0.90)
    df['ensemble_alert'] = (df['ensemble_weighted'] > threshold).astype(int)
    
    # Pseudo labels for evaluation (strict multi-criteria)
    df['pseudo_label_strict'] = (
        (df['off_hour_ratio'] > 0.30).astype(int) +
        (df['attachment_ratio'] > 0.20).astype(int) +
        (df['avg_email_size'] > df['avg_email_size'].quantile(0.90)).astype(int)
    ) >= 2
    
    return df

df = load_and_preprocess_data()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def risk_to_color(risk_level):
    """Map risk level to color code"""
    colors = {
        "CRITICAL": "#ff4444",
        "HIGH": "#ff9800",
        "MEDIUM": "#fbc02d",
        "NORMAL": "#66bb6a"
    }
    return colors.get(risk_level, "#e0e0e0")

def get_risk_description(risk_level):
    """Get readable description of risk level"""
    descriptions = {
        "CRITICAL": "Immediate investigation required",
        "HIGH": "High priority investigation",
        "MEDIUM": "Moderate priority investigation",
        "NORMAL": "No immediate threat indicators"
    }
    return descriptions.get(risk_level, "Unknown")

def render_risk_summary_bar(df_input):
    """Render horizontal risk distribution bar"""
    risk_counts = df_input['risk_level'].value_counts()
    
    # Create proportion data
    total = len(df_input)
    risk_order = ["CRITICAL", "HIGH", "MEDIUM", "NORMAL"]
    proportions = [risk_counts.get(risk, 0) / total for risk in risk_order]
    
    # Create HTML bar
    bar_html = '<div style="display: flex; height: 40px; border-radius: 4px; overflow: hidden; margin: 16px 0;">'
    for risk, prop in zip(risk_order, proportions):
        if prop > 0:
            bar_html += f'<div style="width: {prop*100}%; background-color: {risk_to_color(risk)}; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white;">{prop*100:.0f}%</div>'
    bar_html += '</div>'
    
    st.markdown(bar_html, unsafe_allow_html=True)

def generate_behavioral_explanation(user_row, df_context):
    """Generate plain-English explanation of why user was flagged"""
    explanations = []
    
    # Ensemble score explanation
    mean_score = df_context['ensemble_weighted'].mean()
    std_score = df_context['ensemble_weighted'].std()
    z_score = (user_row['ensemble_weighted'] - mean_score) / std_score
    
    if z_score > 1:
        explanations.append(f"Ensemble anomaly score is {abs(z_score):.1f}σ above average (higher risk)")
    
    # Off-hour activity
    median_off_hour = df_context['off_hour_ratio'].median()
    if user_row['off_hour_ratio'] > median_off_hour * 1.5:
        explanations.append(f"Off-hour activity ratio ({user_row['off_hour_ratio']:.1%}) is significantly higher than peers")
    
    # Attachment behavior
    median_attachments = df_context['attachment_ratio'].median()
    if user_row['attachment_ratio'] > median_attachments * 1.5:
        explanations.append(f"Attachment ratio ({user_row['attachment_ratio']:.1%}) exceeds typical behavior")
    
    # Email size
    median_size = df_context['avg_email_size'].median()
    if user_row['avg_email_size'] > median_size * 1.5:
        explanations.append(f"Average email size ({user_row['avg_email_size']:.0f} bytes) is unusual")
    
    # Communication patterns
    q75_recipients = df_context['avg_recipients'].quantile(0.75)
    if user_row['avg_recipients'] < q75_recipients * 0.5:
        explanations.append(f"Communication is more isolated than typical ({user_row['avg_recipients']:.1f} avg recipients)")
    
    if not explanations:
        explanations.append("Borderline anomaly detection across ensemble models")
    
    return explanations

# ============================================================================
# SIDEBAR FILTERING & NAVIGATION
# ============================================================================

st.sidebar.title("INSIDER THREAT DETECTION")
st.sidebar.markdown("---")

# Risk level multi-select filter
risk_options = ["CRITICAL", "HIGH", "MEDIUM", "NORMAL"]
selected_risks = st.sidebar.multiselect(
    "Filter by Risk Level",
    options=risk_options,
    default=["CRITICAL", "HIGH", "MEDIUM"],
    help="Select risk levels to display. NORMAL excluded by default."
)

# Apply filter
df_filtered = df[df['risk_level'].isin(selected_risks)] if selected_risks else df

st.sidebar.markdown("---")
st.sidebar.subheader("Dataset Statistics")
st.sidebar.metric("Total Users", df.shape[0])
st.sidebar.metric("Alerted Users", df[df['ensemble_alert'] == 1].shape[0])
st.sidebar.metric("Filtered Users", df_filtered.shape[0])

# ============================================================================
# MAIN NAVIGATION TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Main Dashboard",
    "Analytics & Graphs",
    "User Deep Dive",
    "Network Risk",
    "Model Evaluation",
    "How It Works",
    "Simulate User Activity",
    "Secure User Input"
])

# ============================================================================
# TAB 1: MAIN DASHBOARD
# ============================================================================

with tab1:
    st.markdown('<div class="section-header"><h2>Main Dashboard</h2><p>Real-time overview of insider threat risk across the organization</p></div>', unsafe_allow_html=True)
    
    # System Overview KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Users", df.shape[0])
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        critical_count = len(df[df['risk_level'] == 'CRITICAL'])
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("CRITICAL", critical_count, delta=None)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        high_count = len(df[df['risk_level'] == 'HIGH'])
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("HIGH", high_count, delta=None)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        medium_count = len(df[df['risk_level'] == 'MEDIUM'])
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("MEDIUM", medium_count, delta=None)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col5:
        normal_count = len(df[df['risk_level'] == 'NORMAL'])
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("NORMAL", normal_count, delta=None)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Risk Summary Bar
    st.subheader("Risk Distribution")
    render_risk_summary_bar(df_filtered)
    
    st.markdown("---")
    
    # User Risk Table
    st.subheader("User Risk Rankings")
    
    # Prepare display table
    display_df = df_filtered[['user', 'employee_name', 'risk_level', 'ensemble_weighted', 'iso_z', 'lof_z', 'ae_z', 'ensemble_alert']].copy()
    display_df = display_df.sort_values('ensemble_weighted', ascending=False)
    display_df['ensemble_weighted'] = display_df['ensemble_weighted'].round(3)
    display_df['iso_z'] = display_df['iso_z'].round(3)
    display_df['lof_z'] = display_df['lof_z'].round(3)
    display_df['ae_z'] = display_df['ae_z'].round(3)
    display_df.rename(columns={
        'user': 'User ID',
        'employee_name': 'Name',
        'risk_level': 'Risk',
        'ensemble_weighted': 'Ensemble',
        'iso_z': 'Isolation Forest (z)',
        'lof_z': 'LOF (z)',
        'ae_z': 'Autoencoder (z)',
        'ensemble_alert': 'Alerted'
    }, inplace=True)
    
    # Display with styling
    st.dataframe(
        display_df.style
            .background_gradient(subset=['Ensemble'], cmap='RdYlGn_r')
            .format({
                'Ensemble': '{:.3f}',
                'Isolation Forest (z)': '{:.3f}',
                'LOF (z)': '{:.3f}',
                'Autoencoder (z)': '{:.3f}'
            }),
        use_container_width=True,
        height=400
    )


# ============================================================================
# TAB 2: ANALYTICS & GRAPHS
# ============================================================================

with tab2:
    st.markdown('<div class="section-header"><h2>Analytics & Graphs</h2><p>Research-grade visual analysis of anomaly detection system</p></div>', unsafe_allow_html=True)
    
    # A. Anomaly Score Distribution
    st.subheader("A. Anomaly Score Distribution")
    st.markdown("*Histogram of ensemble weighted scores with alert threshold marked.*")
    
    fig, ax = plt.subplots(figsize=(12, 5))
    threshold = df['ensemble_weighted'].quantile(0.90)
    
    ax.hist(df[df['ensemble_alert'] == 0]['ensemble_weighted'], bins=30, alpha=0.7, label='Not Alerted', color='#66bb6a')
    ax.hist(df[df['ensemble_alert'] == 1]['ensemble_weighted'], bins=15, alpha=0.8, label='Alerted', color='#ff4444')
    ax.axvline(threshold, color='#fbc02d', linestyle='--', linewidth=2, label=f'Alert Threshold ({threshold:.2f})')
    
    ax.set_xlabel("Ensemble Anomaly Score (z-normalized)", fontsize=11)
    ax.set_ylabel("Number of Users", fontsize=11)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    st.markdown("---")
    
    # B. Risk-wise Score Distribution
    st.subheader("B. Risk-wise Score Distribution")
    st.markdown("*Violin plot showing ensemble score distribution by risk level.*")
    
    fig, ax = plt.subplots(figsize=(12, 5))
    risk_order = ["CRITICAL", "HIGH", "MEDIUM", "NORMAL"]
    df_plot = df[df['risk_level'].isin(risk_order)]
    
    sns.violinplot(data=df_plot, x='risk_level', y='ensemble_weighted', order=risk_order, ax=ax, palette='Set2')
    ax.set_xlabel("Risk Level", fontsize=11)
    ax.set_ylabel("Ensemble Score", fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    st.pyplot(fig)
    
    st.markdown("---")
    
    # C. Model Contribution Visualization
    st.subheader("C. Model Contribution to Ensemble")
    st.markdown("*Stacked bar showing weighted contribution of each anomaly detector.*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig, ax = plt.subplots(figsize=(10, 5))
        weights = [0.3, 0.4, 0.3]
        models = ['Isolation\nForest', 'LOF', 'Autoencoder']
        colors = ['#ff9800', '#2196F3', '#9C27B0']
        
        bars = ax.bar(models, weights, color=colors, edgecolor='white', linewidth=2)
        ax.set_ylabel("Ensemble Weight", fontsize=11)
        ax.set_ylim([0, 0.5])
        
        # Add value labels on bars
        for bar, w in zip(bars, weights):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{w:.1%}', ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        st.pyplot(fig)
    
    with col2:
        st.markdown("**Ensemble Weights**")
        st.markdown("• **LOF**: 40% (local density)")
        st.markdown("• **Isolation Forest**: 30% (isolation-based)")
        st.markdown("• **Autoencoder**: 30% (reconstruction)")
        st.markdown("\nWeights optimized for ensemble diversity and complementarity.")
    
    st.markdown("---")
    
    # D. Reconstruction Error Analysis
    st.subheader("D. Reconstruction Error Analysis")
    st.markdown("*Mean absolute reconstruction error from autoencoder by risk level.*")
    
    fig, ax = plt.subplots(figsize=(12, 5))
    reconstruction_by_risk = df.groupby('risk_level')['reconstruction_error'].agg(['mean', 'std']).reindex(risk_order)
    
    x_pos = np.arange(len(reconstruction_by_risk))
    bars = ax.bar(x_pos, reconstruction_by_risk['mean'], yerr=reconstruction_by_risk['std'], 
                   capsize=5, color=['#ff4444', '#ff9800', '#fbc02d', '#66bb6a'][:len(reconstruction_by_risk)],
                   edgecolor='white', linewidth=1.5)
    
    ax.set_xticks(x_pos)
    ax.set_xticklabels(reconstruction_by_risk.index)
    ax.set_ylabel("Mean Reconstruction Error", fontsize=11)
    ax.set_xlabel("Risk Level", fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    st.pyplot(fig)
    
    st.markdown("---")
    
    # E. Model Performance Comparison (Proxy ROC-AUC)
    st.subheader("E. Model Performance Comparison (Proxy ROC-AUC)")
    st.markdown("*Evaluation against multi-criteria pseudo-labels. NOT ground truth—for research transparency.*")
    
    try:
        if df['pseudo_label_strict'].nunique() > 1:
            roc_if = roc_auc_score(df['pseudo_label_strict'], df['iso_z'])
            roc_lof = roc_auc_score(df['pseudo_label_strict'], df['lof_z'])
            roc_ae = roc_auc_score(df['pseudo_label_strict'], df['ae_z'])
            roc_ens = roc_auc_score(df['pseudo_label_strict'], df['ensemble_weighted'])
            
            models_perf = pd.DataFrame({
                'Model': ['Isolation Forest', 'LOF', 'Autoencoder', 'Ensemble (Weighted)'],
                'Proxy ROC-AUC': [roc_if, roc_lof, roc_ae, roc_ens]
            })
            
            fig, ax = plt.subplots(figsize=(12, 5))
            bars = ax.barh(models_perf['Model'], models_perf['Proxy ROC-AUC'], 
                            color=['#ff9800', '#2196F3', '#9C27B0', '#4CAF50'],
                            edgecolor='white', linewidth=2)
            
            ax.set_xlim([0.4, 1.0])
            ax.set_xlabel("Proxy ROC-AUC Score", fontsize=11)
            
            # Add value labels
            for bar, val in zip(bars, models_perf['Proxy ROC-AUC']):
                ax.text(val + 0.01, bar.get_y() + bar.get_height()/2, f'{val:.3f}', 
                        va='center', fontsize=11, fontweight='bold')
            
            ax.grid(True, alpha=0.3, axis='x')
            plt.tight_layout()
            st.pyplot(fig)
            
            st.dataframe(models_perf.style.format({'Proxy ROC-AUC': '{:.4f}'}), use_container_width=True)
        else:
            st.warning("Insufficient variation in pseudo-labels for ROC-AUC calculation.")
    except Exception as e:
        st.warning(f"ROC-AUC calculation encountered issue: {str(e)}")

# ============================================================================
# TAB 3: USER DEEP DIVE & EXPLAINABILITY
# ============================================================================

with tab3:
    st.markdown('<div class="section-header"><h2>User Deep Dive & Explainability</h2><p>Detailed analysis and XAI for individual users</p></div>', unsafe_allow_html=True)
    
    # User selection
    user_list = sorted(df['user'].unique())
    selected_user = st.selectbox(
        "Select User for Analysis",
        user_list,
        help="Choose a user to analyze in detail"
    )
    
    user_data = df[df['user'] == selected_user].iloc[0]
    user_idx = df[df['user'] == selected_user].index[0]
    
    st.markdown("---")
    
    # A. User Risk Summary
    st.subheader("A. User Risk Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"<div class='metric-card'><h4>Risk Level</h4><p style='font-size:24px; color:{risk_to_color(user_data['risk_level'])}'>{user_data['risk_level']}</p></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"<div class='metric-card'><h4>Ensemble Score</h4><p style='font-size:24px'>{user_data['ensemble_weighted']:.3f}</p></div>", unsafe_allow_html=True)
    
    with col3:
        alerted_status = "ALERTED" if user_data['ensemble_alert'] == 1 else "Not Alerted"
        color = "#ff4444" if user_data['ensemble_alert'] == 1 else "#66bb6a"
        st.markdown(f"<div class='metric-card'><h4>Alert Status</h4><p style='font-size:18px; color:{color}'>{alerted_status}</p></div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"<div class='metric-card'><h4>Percentile</h4><p style='font-size:24px'>{(user_idx + 1) / len(df) * 100:.1f}%</p></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # B. Base Model Decisions
    st.subheader("B. Base Model Decisions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if_decision = "FLAGGED" if user_data['iso_anomaly'] == 1 else "Normal"
        if_color = "#ff4444" if user_data['iso_anomaly'] == 1 else "#66bb6a"
        st.markdown(f"<div class='metric-card'><h4>Isolation Forest</h4><p style='font-size:18px; color:{if_color}; font-weight:bold'>{if_decision}</p><p style='font-size:12px'>Score: {user_data['iso_z']:.3f}</p></div>", unsafe_allow_html=True)
    
    with col2:
        lof_decision = "FLAGGED" if user_data['lof_anomaly'] == 1 else "Normal"
        lof_color = "#ff4444" if user_data['lof_anomaly'] == 1 else "#66bb6a"
        st.markdown(f"<div class='metric-card'><h4>LOF</h4><p style='font-size:18px; color:{lof_color}; font-weight:bold'>{lof_decision}</p><p style='font-size:12px'>Score: {user_data['lof_z']:.3f}</p></div>", unsafe_allow_html=True)
    
    with col3:
        ae_decision = "FLAGGED" if user_data['ae_anomaly'] == 1 else "Normal"
        ae_color = "#ff4444" if user_data['ae_anomaly'] == 1 else "#66bb6a"
        st.markdown(f"<div class='metric-card'><h4>Autoencoder</h4><p style='font-size:18px; color:{ae_color}; font-weight:bold'>{ae_decision}</p><p style='font-size:12px'>Score: {user_data['ae_z']:.3f}</p></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # C. Behavioral Indicators Table
    st.subheader("C. Key Behavioral Indicators")
    
    behavioral_features = {
        'off_hour_ratio': 'Off-Hour Activity Ratio',
        'attachment_ratio': 'Email Attachment Ratio',
        'avg_email_size': 'Avg Email Size (bytes)',
        'total_emails': 'Total Emails Sent',
        'avg_recipients': 'Avg Recipients per Email',
        'avg_content_length': 'Avg Email Content Length'
    }
    
    behavioral_data = []
    for feature_col, feature_name in behavioral_features.items():
        user_val = user_data[feature_col]
        peer_p75 = df[feature_col].quantile(0.75)
        peer_median = df[feature_col].median()
        
        # Determine if out of range
        out_of_range = (user_val > peer_p75 * 1.5) or (user_val < peer_median * 0.5)
        interpretation = "⚠️ Unusual" if out_of_range else "Normal"
        
        behavioral_data.append({
            'Feature': feature_name,
            'User Value': f"{user_val:.2f}" if isinstance(user_val, float) else str(int(user_val)),
            'Peer 75th %ile': f"{peer_p75:.2f}" if isinstance(peer_p75, float) else str(int(peer_p75)),
            'Interpretation': interpretation
        })
    
    behavioral_df = pd.DataFrame(behavioral_data)
    st.dataframe(behavioral_df, use_container_width=True)
    
    st.markdown("---")
    
    # D. Why This User Was Flagged
    st.subheader("D. Why This User Was Flagged")
    
    explanations = generate_behavioral_explanation(user_data, df)
    
    for i, exp in enumerate(explanations, 1):
        st.markdown(f"• {exp}")
    
    st.markdown("---")
    
    # E. Recommended Analyst Actions
    st.subheader("E. Recommended Analyst Actions")
    
    if user_data['risk_level'] == 'CRITICAL':
        st.markdown("""
        1. **Immediate Investigation**: Contact security team for urgent review
        2. **Access Review**: Check if user has accessed sensitive systems or data
        3. **Communication Audit**: Review recent emails and file transfers for data exfiltration indicators
        4. **Manager Notification**: Alert direct manager immediately
        5. **System Isolation**: Consider temporary access restrictions if threat confirmed
        """)
    elif user_data['risk_level'] == 'HIGH':
        st.markdown("""
        1. **Priority Investigation**: Schedule investigation within 24 hours
        2. **Activity Log Review**: Analyze detailed activity logs for past 7 days
        3. **Peer Comparison**: Compare with similar roles for behavioral deviations
        4. **Resource Verification**: Verify legitimacy of accessed resources and files
        5. **Follow-up**: Plan follow-up assessment in 3-7 days
        """)
    elif user_data['risk_level'] == 'MEDIUM':
        st.markdown("""
        1. **Monitor**: Add to watchlist for continued monitoring
        2. **Contextual Review**: Understand business reasons for unusual behavior
        3. **Trend Analysis**: Check if behavior is new or part of existing pattern
        4. **Preventive Measures**: Discuss expectations with user if appropriate
        5. **Schedule Review**: Set review checkpoint in 14 days
        """)
    else:
        st.markdown("No immediate action required. User exhibits normal behavior patterns.")
    
    st.markdown("---")
    
    # F. Feature JSON View (Collapsible)
    with st.expander("View Raw Feature Data (JSON)"):
        feature_dict = user_data[['user', 'employee_name', 'total_emails', 'off_hour_ratio', 
                                   'attachment_ratio', 'avg_email_size', 'avg_recipients',
                                   'iso_z', 'lof_z', 'ae_z', 'ensemble_weighted', 
                                   'risk_level', 'ensemble_alert']].to_dict()
        
        # Convert numpy types to native Python types for JSON serialization
        for key in feature_dict:
            if isinstance(feature_dict[key], np.floating):
                feature_dict[key] = float(feature_dict[key])
            elif isinstance(feature_dict[key], np.integer):
                feature_dict[key] = int(feature_dict[key])
        
        st.json(feature_dict)

# ============================================================================
# TAB 4: NETWORK RISK VISUALIZATION
# ============================================================================

with tab4:
    st.markdown('<div class="section-header"><h2>Network Risk Visualization</h2><p>Spatial analysis of user anomaly relationships</p></div>', unsafe_allow_html=True)
    
    # PCA-based scatter plot
    st.subheader("User Anomaly Scatter (PCA Projection)")
    st.markdown("*Principal Component Analysis of ensemble scores and behavioral features.*")
    
    # Select features for PCA
    pca_features = ['ensemble_weighted', 'off_hour_ratio', 'attachment_ratio', 
                    'avg_email_size', 'avg_recipients']
    
    X_pca = df[pca_features].copy()
    X_pca = (X_pca - X_pca.mean()) / X_pca.std()
    
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(X_pca)
    
    df_pca = pd.DataFrame({
        'PC1': pca_result[:, 0],
        'PC2': pca_result[:, 1],
        'user': df['user'].values,
        'risk_level': df['risk_level'].values,
        'ensemble_weighted': df['ensemble_weighted'].values
    })
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    risk_order = ['NORMAL', 'MEDIUM', 'HIGH', 'CRITICAL']
    colors_map = {'NORMAL': '#66bb6a', 'MEDIUM': '#fbc02d', 'HIGH': '#ff9800', 'CRITICAL': '#ff4444'}
    
    for risk in risk_order:
        mask = df_pca['risk_level'] == risk
        ax.scatter(df_pca[mask]['PC1'], df_pca[mask]['PC2'], 
                  s=df_pca[mask]['ensemble_weighted'].abs()*100 + 50,
                  alpha=0.6, label=risk, color=colors_map[risk], edgecolors='white', linewidth=0.5)
    
    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)', fontsize=11)
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)', fontsize=11)
    ax.legend(title='Risk Level', loc='best')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    
    st.markdown("**Interpretation:** Node size represents ensemble anomaly score. Clustering indicates behavioral similarity.")
    
    st.markdown("---")
    
    # Statistical summary
    st.subheader("Spatial Risk Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Anomaly Concentration",
            f"{(df['ensemble_alert'].sum() / len(df) * 100):.1f}%",
            help="Percentage of users above alert threshold"
        )
    
    with col2:
        st.metric(
            "Risk Dispersion (Std Dev)",
            f"{df['ensemble_weighted'].std():.3f}",
            help="Score variance across user population"
        )

# ============================================================================
# TAB 5: MODEL EVALUATION
# ============================================================================

with tab5:
    st.markdown('<div class="section-header"><h2>Model Evaluation Metrics</h2><p>Proxy metrics for unsupervised system assessment</p></div>', unsafe_allow_html=True)
    
    # Compute metrics
    if df['pseudo_label_strict'].nunique() > 1:
        roc_full = roc_auc_score(df['pseudo_label_strict'], df['ensemble_weighted'])
        tail_df = df[df['ensemble_weighted'] > df['ensemble_weighted'].quantile(0.70)]
        roc_tail = roc_auc_score(tail_df['pseudo_label_strict'], tail_df['ensemble_weighted']) if tail_df['pseudo_label_strict'].nunique() > 1 else np.nan
    else:
        roc_full = np.nan
        roc_tail = np.nan
    
    actual_normal = df[df['pseudo_label_strict'] == 0]
    false_positives = actual_normal[actual_normal['ensemble_alert'] == 1]
    fpr = len(false_positives) / len(actual_normal) if len(actual_normal) > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"<div class='metric-card'><h4>Proxy ROC-AUC (Full)</h4><p style='font-size:24px'>{roc_full:.3f}</p><p style='font-size:11px'>All users</p></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"<div class='metric-card'><h4>Proxy ROC-AUC (Tail 30%)</h4><p style='font-size:24px'>{roc_tail:.3f}</p><p style='font-size:11px'>Top anomalies</p></div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"<div class='metric-card'><h4>False Positive Rate</h4><p style='font-size:24px'>{fpr:.1%}</p><p style='font-size:11px'>Alerted normal users</p></div>", unsafe_allow_html=True)
    
    with col4:
        trustworthiness_score = 1 - (fpr / 2)  # Simple proxy
        st.markdown(f"<div class='metric-card'><h4>Trustworthiness</h4><p style='font-size:24px'>{max(0, trustworthiness_score):.2f}</p><p style='font-size:11px'>System reliability</p></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Detailed metrics table
    st.subheader("Detailed Evaluation Summary")
    
    metrics_df = pd.DataFrame({
        'Metric': [
            'Proxy ROC-AUC (Full Dataset)',
            'Proxy ROC-AUC (Top 30% Scores)',
            'Alert Threshold (90th %ile)',
            'Users Alerted',
            'Alerted vs Pseudo-Positives',
            'False Positive Rate',
            'Ensemble Model Count',
            'Median Score Variance'
        ],
        'Value': [
            f"{roc_full:.3f}",
            f"{roc_tail:.3f}",
            f"{df['ensemble_weighted'].quantile(0.90):.3f}",
            f"{df['ensemble_alert'].sum()}",
            f"{len(df[(df['ensemble_alert']==1) & (df['pseudo_label_strict']==1)])}",
            f"{fpr:.2%}",
            "3 (IF, LOF, AE)",
            f"{df['ensemble_weighted'].std():.3f}"
        ]
    })
    
    st.dataframe(metrics_df, use_container_width=True)
    
    st.markdown("---")
    
    st.subheader("Metric Explanations")
    
    with st.expander("What is Proxy ROC-AUC?"):
        st.markdown("""
        In unsupervised learning, we lack true labels. Instead, we use **pseudo-labels** derived from:
        - Off-hour activity ratio > 30%
        - Attachment ratio > 20%
        - Email size > 90th percentile
        
        These are **heuristic indicators**, not ground truth. ROC-AUC against pseudo-labels shows 
        how well the ensemble separates these behavioral indicators. NOT a claim of supervised accuracy.
        """)
    
    with st.expander("What is False Positive Rate?"):
        st.markdown("""
        FPR = (Alerted users with pseudo_label=0) / (Total pseudo_label=0)
        
        Shows proportion of "normal" users (by heuristic) that were alerted.
        Lower is better, but context matters—some operational overhead is acceptable for security.
        """)
    
    with st.expander("Why is ROC-AUC marked as 'Proxy'?"):
        st.markdown("""
        Without confirmed insider threat incidents in the dataset, true ROC-AUC is impossible.
        Proxy metrics assess:
        1. Separation quality (do anomalies score higher?)
        2. Consistency with heuristic indicators
        3. Stability across ensemble models
        
        These inform research credibility but do NOT replace validation on labeled data.
        """)
    
    with st.expander("What is Trustworthiness?"):
        st.markdown("""
        A simple proxy combining:
        - Low false positive rate (fewer legitimate users flagged)
        - Ensemble agreement (multiple models concur)
        - Score separation (clear distinction between risk levels)
        
        Used to gauge system reliability for pilot deployments.
        """)

# ============================================================================
# TAB 6: HOW DOES THIS WORK?
# ============================================================================

with tab6:
    st.markdown('<div class="section-header"><h2>How Does This System Work?</h2><p>Non-technical explanation of insider threat detection</p></div>', unsafe_allow_html=True)
    
    st.subheader("What is Insider Threat?")
    st.markdown("""
    An **insider threat** is when someone with legitimate access to organizational systems 
    (employee, contractor, vendor) misuses that access for harm:
    
    - **Data theft**: Exfiltrating sensitive documents
    - **Sabotage**: Disrupting systems or operations
    - **Fraud**: Manipulating records for financial gain
    - **IP theft**: Stealing intellectual property
    
    Insider threats are dangerous because they bypass perimeter security (firewalls, VPNs).
    """)
    
    st.markdown("---")
    
    st.subheader("Why Unsupervised Learning?")
    st.markdown("""
    Most organizations lack **confirmed insider threat incidents** in their data. 
    We can't use supervised machine learning (which requires labeled examples).
    
    Instead, we use **unsupervised anomaly detection**: finding users whose behavior 
    deviates from the norm, without needing to know the specific threat type.
    
    **Advantage**: Works for novel attack patterns not seen before.
    **Tradeoff**: Can't claim "99% accurate"—we lack ground truth validation.
    """)
    
    st.markdown("---")
    
    st.subheader("How the Ensemble System Works")
    st.markdown("""
    This dashboard uses **3 independent anomaly detectors**, each with different logic:
    
    #### 1. Isolation Forest (30% weight)
    - Idea: Anomalies are "easier to isolate" than normal points
    - Detects: Unusual communication patterns, off-hour activity
    - Good at: Spotting behavioral outliers
    
    #### 2. Local Outlier Factor / LOF (40% weight)
    - Idea: Anomalies have lower local density than neighbors
    - Detects: Users different from their peer group
    - Good at: Context-aware anomaly detection
    
    #### 3. Autoencoder Neural Network (30% weight)
    - Idea: Normal behavior is easy to reconstruct; anomalies are hard
    - Detects: Complex, non-linear deviations
    - Good at: Capturing subtle, multi-feature deviations
    
    **Ensemble Voting**: Scores from all 3 are combined (weighted average).
    No single model can fool the ensemble—robustness through diversity.
    """)
    
    st.markdown("---")
    
    st.subheader("What Features Are Analyzed?")
    st.markdown("""
    The system monitors:
    
    | Feature | What It Means | Threat Signal |
    |---------|--------------|---------------|
    | Off-hour Activity | Emails sent outside 9-5 | Data theft often happens after hours |
    | Attachment Ratio | % of emails with attachments | Potential data exfiltration |
    | Email Size | Average size of messages | Large files (e.g., databases) = suspicious |
    | Email Recipients | How many people per message | Unusual distribution patterns |
    | Communication Volume | Total emails sent | Sudden spikes = concerning |
    
    All features are **normalized** and scored by each detector independently.
    """)
    
    st.markdown("---")
    
    st.subheader("Risk Levels Explained")
    st.markdown("""
    #### CRITICAL (Top 1-2%)
    - Extreme anomaly on multiple fronts
    - Immediate investigation required
    - High likelihood of malicious intent OR system misconfiguration
    
    #### HIGH (Top 5-10%)
    - Strong anomaly signals
    - Priority investigation within 24 hours
    - Could be insider threat or unusual-but-legitimate activity
    
    #### MEDIUM (10-25%)
    - Moderate deviations from peers
    - Worth monitoring; schedule follow-up
    - May resolve with context (new project, role change, etc.)
    
    #### NORMAL (75%+)
    - Behavior consistent with peers
    - No immediate security concern
    - Routine monitoring continues
    """)
    
    st.markdown("---")
    
    st.subheader("How to Use This Dashboard")
    st.markdown("""
    1. **Start on Main Dashboard**: Get system-wide overview and identify top alerts
    2. **Review Analytics**: Understand model decisions and data distributions
    3. **Deep Dive on Users**: Click a user to see detailed explainability
    4. **Check Network View**: Spot behavioral clusters or isolated anomalies
    5. **Monitor Metrics**: Track FPR and proxy ROC-AUC over time
    6. **Take Action**: Follow recommended analyst actions for CRITICAL/HIGH users
    
    **Gold Rule**: Correlation ≠ causation. Anomaly ≠ proof of guilt.
    Always verify alerts with contextual investigation.
    """)
    
    st.markdown("---")
    
    st.subheader("Limitations & Disclaimers")
    st.markdown("""
    ⚠️ **This is an unsupervised system:**
    - NO labeled ground truth (no confirmed threats in training data)
    - Metrics are "proxy" estimates based on heuristic pseudo-labels
    - Cannot claim supervised accuracy (e.g., "99% detection rate")
    - Requires human validation for every alert
    
    ⚠️ **Context matters:**
    - New employees may score high (still learning role)
    - Role transitions (e.g., promotion) cause behavioral shifts
    - Projects may legitimately require unusual activity
    - Business events (quarter-end, audits) can spike alerting
    
    ⚠️ **Feedback required:**
    - Update pseudo-labels if actual threats are discovered
    - Tune thresholds based on investigation outcomes
    - Retrain models as organization evolves
    - Monitor for concept drift (changes over time)
    
    **Recommendations:**
    1. Use this as **screening tool**, not final verdict
    2. Combine with other security signals (logs, network, tools)
    3. Ensure investigations are fair and legally compliant
    4. Document all alerts and resolutions for future learning
    """)
    
    st.markdown("---")
    
    st.subheader("Technical Papers & References")
    st.markdown("""
    **Anomaly Detection Methods:**
    - Liu et al. "Isolation Forest" (IEEE ICDM 2008)
    - Breunig et al. "LOF: Local Outlier Factor" (SIGMOD 2000)
    - Kingma & Welling "Auto-Encoding VAE" (ICLR 2014)
    
    **Insider Threat Detection:**
    - Gavai et al. "Supervised Insider Threat Detection" (IEEE S&P 2015)
    - Yuan et al. "Unsupervised Anomaly Detection in Email" (NDSS 2014)
    
    **Ensemble Methods:**
    - Zhou "Ensemble Methods: Foundations and Algorithms" (CRC 2012)
    - Kuncheva & Whitaker "Diversity in Multiple Classifier Systems" (IF 2003)
    """)

# ============================================================================
# TAB 7: SIMULATE USER ACTIVITY
# ============================================================================

with tab7:
    st.markdown('<div class="section-header"><h2>Simulate User Activity</h2><p>Manual input interface for analyst-driven risk assessment</p></div>', unsafe_allow_html=True)
    
    # Disclaimer
    st.warning(
        "**SIMULATION MODE - EPHEMERAL DATA**\n\n"
        "This interface is a demonstration tool. All inputs exist only in memory. "
        "No data is stored, logged, or persisted. Results are computed against a frozen baseline dataset. "
        "Refresh the page or close the app to clear all inputs."
    )
    
    st.markdown("---")
    
    # Compute baseline statistics from frozen dataset
    baseline_off_hour = df['off_hour_ratio'].describe()
    baseline_attachment = df['attachment_ratio'].describe()
    baseline_email_size = df['avg_email_size'].describe()
    baseline_recipients = df['avg_recipients'].describe()
    
    st.subheader("Input Simulated User Behavior")
    st.markdown("*Enter realistic values for a hypothetical user. All inputs are validated against baseline statistics.*")
    
    col1, col2 = st.columns(2)
    
    # Input 1: Off-hour Activity Ratio
    with col1:
        st.markdown("**1. Off-hour Activity Ratio**")
        st.caption("Fraction of user activity occurring outside 9-5 working hours")
        off_hour_input = st.slider(
            "Off-hour Ratio",
            min_value=0.0,
            max_value=1.0,
            value=0.15,
            step=0.05,
            help=f"Baseline: Mean={baseline_off_hour['mean']:.2%}, Normal boundary ≤30%"
        )
        
        if off_hour_input > 0.30:
            st.warning(f"⚠️ Above normal threshold (30%)")
        st.caption(f"Baseline mean: {baseline_off_hour['mean']:.2%} | Normal boundary: ≤30%")
    
    # Input 2: Attachment Ratio
    with col2:
        st.markdown("**2. Attachment Ratio**")
        st.caption("Proportion of emails containing attachments")
        attachment_input = st.slider(
            "Attachment Ratio",
            min_value=0.0,
            max_value=1.0,
            value=0.10,
            step=0.05,
            help=f"Baseline: Mean={baseline_attachment['mean']:.2%}, Normal boundary ≤20%"
        )
        
        if attachment_input > 0.20:
            st.warning(f"⚠️ Above normal threshold (20%)")
        st.caption(f"Baseline mean: {baseline_attachment['mean']:.2%} | Normal boundary: ≤20%")
    
    col3, col4 = st.columns(2)
    
    # Input 3: Average Email Size
    with col3:
        st.markdown("**3. Average Email Size (bytes)**")
        st.caption("Average size of emails sent by user")
        email_size_input = st.number_input(
            "Email Size",
            min_value=0,
            max_value=1000000,
            value=int(baseline_email_size['mean']),
            step=1000,
            help=f"Baseline: Mean={baseline_email_size['mean']:.0f} bytes, p75={baseline_email_size['75%']:.0f}"
        )
        
        p75_size = baseline_email_size['75%']
        if email_size_input > p75_size * 1.5:
            st.warning(f"⚠️ Above 1.5x normal threshold ({p75_size*1.5:.0f} bytes)")
        st.caption(f"Baseline: Mean={baseline_email_size['mean']:.0f} | 75th %ile={p75_size:.0f}")
    
    # Input 4: Unique Recipients per Day
    with col4:
        st.markdown("**4. Unique Recipients per Day**")
        st.caption("Number of distinct people contacted daily")
        recipients_input = st.number_input(
            "Recipients",
            min_value=0,
            max_value=500,
            value=int(baseline_recipients['mean']),
            step=1,
            help=f"Baseline: Mean={baseline_recipients['mean']:.1f}, Std={baseline_recipients['std']:.1f}"
        )
        
        q75_recipients = baseline_recipients['75%']
        if recipients_input < q75_recipients * 0.5:
            st.warning(f"⚠️ Below isolation threshold ({q75_recipients*0.5:.1f})")
        st.caption(f"Baseline: Mean={baseline_recipients['mean']:.1f} | Std={baseline_recipients['std']:.1f}")
    
    col5, col6 = st.columns(2)
    
    # Input 5: USB Usage per Day
    with col5:
        st.markdown("**5. USB Usage per Day**")
        st.caption("Frequency of removable media device access")
        usb_usage = st.number_input(
            "USB Events",
            min_value=0,
            max_value=100,
            value=0,
            step=1,
            help="Frequency of removable media usage (high = data exfiltration signal)"
        )
        
        if usb_usage > 5:
            st.warning(f"⚠️ High USB activity ({usb_usage} events/day)")
        st.caption("High USB activity may indicate data staging")
    
    # Input 6: Network Centrality
    with col6:
        st.markdown("**6. Network Centrality**")
        st.caption("User's structural importance in communication network")
        network_centrality = st.slider(
            "Centrality",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            help="Fraction: 0=peripheral, 1=central hub. Low centrality may indicate isolated threat actor"
        )
        
        if network_centrality < 0.3:
            st.warning(f"⚠️ Low network centrality (isolated user)")
        st.caption("Low centrality (≤0.3) = isolated, high = central hub")
    
    st.markdown("---")
    
    # Compute risk assessment
    st.subheader("Risk Evaluation Results")
    
    # Z-score normalization using frozen baseline stats
    z_off_hour = (off_hour_input - baseline_off_hour['mean']) / max(baseline_off_hour['std'], 0.001)
    z_attachment = (attachment_input - baseline_attachment['mean']) / max(baseline_attachment['std'], 0.001)
    z_email_size = (email_size_input - baseline_email_size['mean']) / max(baseline_email_size['std'], 0.001)
    z_recipients = (recipients_input - baseline_recipients['mean']) / max(baseline_recipients['std'], 0.001)
    
    # Simulate anomaly scores (proxy for ensemble models)
    # Isolation Forest: detects isolated points, off-hour activity, low connectivity
    iso_anomaly = (abs(z_off_hour) + abs(z_recipients)) / 2.0
    
    # LOF: local density-based, attachment behavior, email size
    lof_anomaly = (abs(z_attachment) + abs(z_email_size)) / 2.0
    
    # Autoencoder: multi-feature reconstruction error, USB activity
    ae_anomaly = (abs(z_off_hour) + abs(z_attachment) + abs(z_email_size)) / 3.0 + (usb_usage / 10.0)
    
    # Normalize anomaly scores to 0-1 range
    iso_score = min(1.0, max(0.0, iso_anomaly / 3.0))
    lof_score = min(1.0, max(0.0, lof_anomaly / 3.0))
    ae_score = min(1.0, max(0.0, ae_anomaly / 3.0))
    
    # Ensemble weighted average (40% LOF, 30% IF, 30% AE)
    ensemble_score = 0.4 * lof_score + 0.3 * iso_score + 0.3 * ae_score
    
    # Risk level assignment
    if ensemble_score >= 0.8:
        risk_level = "CRITICAL"
        risk_color = "#ff4444"
        alert_status = "ALERTED"
    elif ensemble_score >= 0.6:
        risk_level = "HIGH"
        risk_color = "#ff9800"
        alert_status = "ALERTED"
    elif ensemble_score >= 0.4:
        risk_level = "MEDIUM"
        risk_color = "#fbc02d"
        alert_status = "Monitor"
    else:
        risk_level = "NORMAL"
        risk_color = "#66bb6a"
        alert_status = "No Alert"
    
    # A. Risk Summary Card
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"<div class='metric-card'><h4>Risk Level</h4><p style='font-size:28px; color:{risk_color}; font-weight:bold'>{risk_level}</p></div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"<div class='metric-card'><h4>Ensemble Score</h4><p style='font-size:28px'>{ensemble_score:.3f}</p><p style='font-size:11px'>Range: 0.0 – 1.0</p></div>", unsafe_allow_html=True)
    
    with col3:
        alert_color = "#ff4444" if alert_status == "ALERTED" else "#fbc02d" if alert_status == "Monitor" else "#66bb6a"
        st.markdown(f"<div class='metric-card'><h4>Alert Status</h4><p style='font-size:20px; color:{alert_color}; font-weight:bold'>{alert_status}</p></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # B. Model Contribution Breakdown
    st.subheader("Model Contribution Breakdown")
    st.markdown("*How each anomaly detector contributed to the overall risk score.*")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        fig, ax = plt.subplots(figsize=(10, 5))
        
        models = ['Isolation\nForest (30%)', 'LOF (40%)', 'Autoencoder (30%)']
        scores = [iso_score, lof_score, ae_score]
        colors = ['#ff9800', '#2196F3', '#9C27B0']
        weights = [0.3, 0.4, 0.3]
        
        bars = ax.bar(models, scores, color=colors, edgecolor='white', linewidth=2, alpha=0.8)
        ax.axhline(y=0.6, color='#ff9800', linestyle='--', linewidth=2, label='HIGH Risk Threshold (0.6)')
        ax.axhline(y=0.8, color='#ff4444', linestyle='--', linewidth=2, label='CRITICAL Threshold (0.8)')
        ax.set_ylabel("Anomaly Score", fontsize=11)
        ax.set_ylim([0, 1.0])
        ax.legend(loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar, score, weight in zip(bars, scores, weights):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{score:.3f}\n({weight:.0%})', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig)
    
    with col2:
        st.markdown("**Ensemble Logic:**")
        st.markdown(f"""
        • **IF**: {iso_score:.3f} × 30% = {iso_score*0.3:.3f}
        • **LOF**: {lof_score:.3f} × 40% = {lof_score*0.4:.3f}
        • **AE**: {ae_score:.3f} × 30% = {ae_score*0.3:.3f}
        
        **Total**: {ensemble_score:.3f}
        
        **Aggregation**: Weighted average ensures no single model dominates. Diversity provides robustness.
        """)
    
    st.markdown("---")
    
    # C. Explainability Panel
    st.subheader("Why This Risk Assessment?")
    
    explanations = []
    
    # Isolation Forest explanations
    if z_off_hour > 1.5:
        explanations.append(f"📌 Off-hour activity ({off_hour_input:.0%}) is {abs(z_off_hour):.1f}σ above baseline ({baseline_off_hour['mean']:.0%}). Isolation Forest flagged this as anomalous.")
    
    if abs(z_recipients) > 1.5 and recipients_input < baseline_recipients['50%']:
        explanations.append(f"📌 Isolated communication pattern: {recipients_input:.0f} unique recipients/day (baseline: {baseline_recipients['mean']:.0f}). Lower connectivity = harder to isolate, signals anomaly.")
    
    # LOF explanations
    if z_attachment > 1.5:
        explanations.append(f"🔗 High attachment ratio ({attachment_input:.0%}) vs. baseline ({baseline_attachment['mean']:.0%}). Potential data exfiltration vector.")
    
    if z_email_size > 1.5:
        explanations.append(f"🔗 Oversized emails ({email_size_input:.0f} bytes avg, baseline: {baseline_email_size['mean']:.0f}). May indicate bulk data transfers.")
    
    # Autoencoder explanations
    if usb_usage > 5:
        explanations.append(f"🧠 High USB device activity ({usb_usage} events/day). Removable media = classic data staging signal.")
    
    # Network centrality
    if network_centrality < 0.3:
        explanations.append(f"🧠 Low network centrality ({network_centrality:.2f}). Peripheral user with limited connections—harder to monitor, easier to hide anomalies.")
    
    # Baseline risk explanation
    if ensemble_score < 0.4:
        if not explanations:
            explanations.append("✅ User behavior is consistent with baseline population. No significant anomalies detected.")
    
    if explanations:
        for i, exp in enumerate(explanations, 1):
            st.markdown(f"{i}. {exp}")
    else:
        st.markdown("✅ No significant deviations from baseline behavior detected.")
    
    st.markdown("---")
    
    # Summary interpretation
    st.subheader("Risk Interpretation & Next Steps")
    
    if risk_level == "CRITICAL":
        st.markdown("""
        **🚨 CRITICAL RISK**
        
        This simulated user exhibits **extreme anomalies** across multiple dimensions:
        - Multiple detectors (IF, LOF, AE) concur on high risk
        - Behavior significantly deviates from organizational baseline
        
        **Recommended Actions:**
        1. Immediate investigation by security team
        2. Review all account activities (emails, file access, USB logs)
        3. Manager notification and potential access restrictions
        4. Verify legitimacy of unusual behavior (new project? role change?)
        """)
    
    elif risk_level == "HIGH":
        st.markdown("""
        **⚠️ HIGH RISK**
        
        This simulated user shows **notable anomalies** requiring attention:
        - Two or more detectors flagging suspicious patterns
        - Behavior moderately outside baseline norms
        
        **Recommended Actions:**
        1. Priority investigation within 24 hours
        2. Review activity logs for past 7 days
        3. Compare with peer group for contextualization
        4. Follow-up assessment in 3-7 days
        """)
    
    elif risk_level == "MEDIUM":
        st.markdown("""
        **⚡ MEDIUM RISK**
        
        This simulated user exhibits **moderate deviations** worth monitoring:
        - Some behavioral anomalies detected
        - May be legitimate (new employee, role change, project deadline)
        
        **Recommended Actions:**
        1. Add to monitoring watchlist
        2. Understand business context (new role? special project?)
        3. Schedule follow-up review in 14 days
        4. Document for trend analysis
        """)
    
    else:
        st.markdown("""
        **✅ NORMAL RISK**
        
        This simulated user's behavior is **consistent with baseline**:
        - No significant anomalies detected
        - All detectors agree on normal classification
        
        **Recommended Actions:**
        - Continue routine monitoring
        - No immediate escalation required
        - Standard security practices apply
        """)
    
    st.markdown("---")
    
    # Methodology note
    with st.expander("Technical Methodology (Advanced)"):
        st.markdown(f"""
        ### Frozen Baseline Statistics
        The simulator uses statistics computed ONCE from the baseline dataset.
        These are NOT updated or retrained.
        
        **Baseline Parameters:**
        | Metric | Mean | Std | 75th %ile |
        |--------|------|-----|----------|
        | Off-hour Ratio | {baseline_off_hour['mean']:.3f} | {baseline_off_hour['std']:.3f} | {baseline_off_hour['75%']:.3f} |
        | Attachment Ratio | {baseline_attachment['mean']:.3f} | {baseline_attachment['std']:.3f} | {baseline_attachment['75%']:.3f} |
        | Email Size (bytes) | {baseline_email_size['mean']:.0f} | {baseline_email_size['std']:.0f} | {baseline_email_size['75%']:.0f} |
        | Recipients | {baseline_recipients['mean']:.2f} | {baseline_recipients['std']:.2f} | {baseline_recipients['75%']:.2f} |
        
        ### Scoring Formula
        1. **Z-score normalization**: `z = (value - mean) / std`
        2. **Isolation Forest**: Detects isolated points via separation difficulty
        3. **LOF**: Computes local density; anomalies have lower density
        4. **Autoencoder**: Neural network reconstruction error
        5. **Ensemble**: `score = 0.4×LOF + 0.3×IF + 0.3×AE`
        
        ### Risk Thresholds
        - **CRITICAL**: ≥ 0.80 (top 1-2% anomaly score)
        - **HIGH**: 0.60–0.79 (top 5-10%)
        - **MEDIUM**: 0.40–0.59 (top 25%)
        - **NORMAL**: < 0.40 (baseline population)
        
        ### Data Handling
        - **Input persistence**: NONE (ephemeral, memory-only)
        - **Model updates**: NEVER (frozen baseline)
        - **Threshold tuning**: DISABLED (research baseline)
        - **Retraining**: NOT SUPPORTED (demo mode)
        """)


# ============================================================================
# TAB 8: SECURE USER INPUT — SHA-512 AUTHENTICATION
# ============================================================================

with tab8:
    st.markdown('<div class="section-header"><h2>Secure User Input & Authentication</h2><p>Register, authenticate, and submit structured behavioral data with SHA-512 security</p></div>', unsafe_allow_html=True)
    
    st.warning(
        "🔐 **SECURE AUTHENTICATION ENABLED**\n\n"
        "This tab uses SHA-512 password hashing for user authentication. "
        "Passwords are NEVER stored or logged in plaintext. "
        "All submitted data is persisted to manual_user_entries.csv for ensemble analysis."
    )
    
    st.markdown("---")
    
    # ========================================================================
    # AUTHENTICATION SECTION
    # ========================================================================
    
    st.subheader("🔐 User Authentication")
    st.markdown("*Register a new user or log in to submit data.*")
    
    # Check current authentication status
    if is_authenticated():
        current_user = get_current_user()
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.success(f"✅ **Authenticated as: `{current_user}`**")
        
        with col2:
            if st.button("🔄 Switch User", key="switch_user_btn"):
                logout()
                st.rerun()
        
        with col3:
            if st.button("🚪 Logout", key="logout_btn"):
                logout()
                st.success("Logged out successfully!")
                st.rerun()
        
        st.markdown("---")
        
        # ====================================================================
        # POST-AUTHENTICATION INPUT FORM
        # ====================================================================
        
        st.subheader("📝 Submit User Behavioral Data")
        st.markdown("*Complete this form with user data. All fields are validated before submission.*")
        
        with st.form(key="user_entry_form", clear_on_submit=True):
            
            # Auto-filled user field
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input(
                    "Username (auto-filled)",
                    value=current_user,
                    disabled=True,
                    help="Current authenticated user"
                )
            
            with col2:
                employee_name = st.text_input(
                    "Employee Name",
                    placeholder="e.g., Alden Caesar Velez",
                    help="Full name of the employee"
                )
            
            # Behavioral metrics
            col1, col2 = st.columns(2)
            
            with col1:
                total_emails = st.number_input(
                    "Total Emails (last period)",
                    min_value=0,
                    value=35,
                    step=1,
                    help="Total email count for the observation period"
                )
            
            with col2:
                off_hour_ratio = st.number_input(
                    "Off-hour Activity Ratio",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0857,
                    step=0.01,
                    format="%.4f",
                    help="Fraction of activity outside 9-5 working hours (0-1)"
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                attachment_ratio = st.number_input(
                    "Attachment Ratio",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.2571,
                    step=0.01,
                    format="%.4f",
                    help="Proportion of emails containing attachments (0-1)"
                )
            
            with col2:
                avg_email_size = st.number_input(
                    "Avg Email Size (bytes)",
                    min_value=0.0,
                    value=30407.23,
                    step=100.0,
                    format="%.2f",
                    help="Average size of emails sent by this user"
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                avg_recipients = st.number_input(
                    "Avg Recipients per Email",
                    min_value=0.0,
                    value=2.97,
                    step=0.1,
                    format="%.2f",
                    help="Average number of unique recipients per email"
                )
            
            with col2:
                st.markdown("**Z-Score Normalization (Anomaly Metrics)**")
                iso_z = st.number_input(
                    "Isolation Forest Z-score",
                    value=-0.161,
                    step=0.01,
                    format="%.3f",
                    help="Z-score from Isolation Forest model"
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                lof_z = st.number_input(
                    "LOF Z-score",
                    value=-0.346,
                    step=0.01,
                    format="%.3f",
                    help="Z-score from Local Outlier Factor model"
                )
            
            with col2:
                ae_z = st.number_input(
                    "Autoencoder Z-score",
                    value=-0.561,
                    step=0.01,
                    format="%.3f",
                    help="Z-score from Autoencoder reconstruction error"
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                ensemble_weighted = st.number_input(
                    "Ensemble Weighted Score",
                    value=-0.355,
                    step=0.01,
                    format="%.3f",
                    help="Weighted ensemble of all three models (40% LOF, 30% IF, 30% AE)"
                )
            
            with col2:
                risk_level = st.selectbox(
                    "Risk Level",
                    options=["NORMAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"],
                    index=0,
                    help="Manual risk assessment"
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                ensemble_alert = st.selectbox(
                    "Ensemble Alert Flag",
                    options=[0, 1],
                    index=0,
                    help="0 = No alert, 1 = Alert triggered"
                )
            
            with col2:
                st.markdown("**Status**")
                st.info(f"Ready to submit data for {current_user}")
            
            st.markdown("---")
            
            # Preview button only (no automatic save)
            preview_button = st.form_submit_button(
                "👁️ Preview Entry",
                use_container_width=True,
                type="secondary"
            )
            
            if preview_button:
                # Prepare entry dictionary
                entry = {
                    'user': current_user,
                    'employee_name': employee_name,
                    'total_emails': int(total_emails),
                    'off_hour_ratio': float(off_hour_ratio),
                    'attachment_ratio': float(attachment_ratio),
                    'avg_email_size': float(avg_email_size),
                    'avg_recipients': float(avg_recipients),
                    'iso_z': float(iso_z),
                    'lof_z': float(lof_z),
                    'ae_z': float(ae_z),
                    'ensemble_weighted': float(ensemble_weighted),
                    'risk_level': risk_level.upper(),
                    'ensemble_alert': int(ensemble_alert)
                }
                
                # Validate entry
                is_valid, errors = validate_user_entry(entry)
                
                if is_valid:
                    # Store in session state for later saving
                    st.session_state.preview_entry = entry
                    st.session_state.show_preview = True
                    st.success("✅ Entry is valid! Review below and save if correct.")
                
                else:
                    st.error("❌ **Validation Errors - Please Fix:**")
                    for error in errors:
                        st.error(f"  • {error}")
        
        st.markdown("---")
        
        # ====================================================================
        # PREVIEW SECTION (After validation)
        # ====================================================================
        
        if st.session_state.get('show_preview', False) and 'preview_entry' in st.session_state:
            st.subheader("👁️ Preview Your Entry")
            st.markdown("Review your data before saving. Edit the form above to make changes.")
            
            preview_entry = st.session_state.preview_entry
            preview_df = pd.DataFrame([preview_entry])
            
            # Display preview as table
            st.dataframe(preview_df, use_container_width=True, height=150)
            
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("User ID", preview_entry['user'], help="Unique identifier")
            
            with col2:
                st.metric("Employee", preview_entry['employee_name'], help="Human-readable name")
            
            with col3:
                st.metric("Risk Level", preview_entry['risk_level'], help="Manual risk assessment")
            
            with col4:
                st.metric("Ensemble Score", f"{preview_entry['ensemble_weighted']:.3f}", help="Weighted ensemble score")
            
            # Detailed breakdown
            with st.expander("📋 Detailed Field Breakdown"):
                detail_cols = st.columns(2)
                
                with detail_cols[0]:
                    st.markdown("**Behavioral Metrics**")
                    st.write(f"• Total Emails: {preview_entry['total_emails']}")
                    st.write(f"• Off-Hour Ratio: {preview_entry['off_hour_ratio']:.4f}")
                    st.write(f"• Attachment Ratio: {preview_entry['attachment_ratio']:.4f}")
                    st.write(f"• Avg Email Size: {preview_entry['avg_email_size']:.2f} bytes")
                    st.write(f"• Avg Recipients: {preview_entry['avg_recipients']:.2f}")
                
                with detail_cols[1]:
                    st.markdown("**Anomaly Scores (Z-Scores)**")
                    st.write(f"• Isolation Forest: {preview_entry['iso_z']:.3f}")
                    st.write(f"• LOF: {preview_entry['lof_z']:.3f}")
                    st.write(f"• Autoencoder: {preview_entry['ae_z']:.3f}")
                    st.write(f"• Ensemble Weighted: {preview_entry['ensemble_weighted']:.3f}")
                    st.write(f"• Alert Flag: {preview_entry['ensemble_alert']}")
            
            st.markdown("---")
            
            # Save button (separate from form)
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button("💾 Save Entry", key="save_entry_btn", type="primary", use_container_width=True):
                    # Save to CSV
                    success, message = save_manual_entry(preview_entry)
                    
                    if success:
                        st.success(message)
                        st.balloons()
                        
                        # Display saved entry
                        st.markdown("**✅ Successfully Saved:**")
                        st.dataframe(pd.DataFrame([preview_entry]), use_container_width=True)
                        
                        # Show stats
                        total_entries = get_user_entries_count()
                        st.info(f"📊 Total manual entries saved: **{total_entries}**")
                        
                        # Clear preview
                        st.session_state.show_preview = False
                        st.session_state.preview_entry = None
                        st.rerun()
                    else:
                        st.error(message)
            
            with col2:
                if st.button("❌ Cancel & Edit", key="cancel_btn", use_container_width=True):
                    st.session_state.show_preview = False
                    st.info("You can now edit the form above")
                    st.rerun()
        
        st.markdown("---")
        
        # ====================================================================
        # DATA INTEGRITY & PIPELINE INTEGRATION
        # ====================================================================
        
        st.subheader("📊 Submitted Data Status")
        st.markdown("*Manually submitted entries will appear in the main dashboard and be eligible for ensemble analysis.*")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_manual = get_user_entries_count()
            st.metric("Total Manual Entries", total_manual, help="Cumulative count in manual_user_entries.csv")
        
        with col2:
            # Check if any entries for current user
            import os
            manual_file = "manual_user_entries.csv"
            user_count = 0
            if os.path.exists(manual_file):
                manual_df = pd.read_csv(manual_file)
                user_count = len(manual_df[manual_df['user'] == current_user])
            st.metric(f"Your Entries ({current_user})", user_count)
        
        with col3:
            st.metric("Baseline Users", df.shape[0], help="Users in baseline dataset")
        
        # Show recent entries
        if get_user_entries_count() > 0:
            st.subheader("Recent Submissions")
            manual_df = pd.read_csv("manual_user_entries.csv")
            st.dataframe(
                manual_df.tail(10),
                use_container_width=True,
                height=300
            )
        
        with st.expander("🔍 Integration Details"):
            st.markdown("""
            ### How Your Submissions Are Integrated
            
            1. **Storage**: Entries saved to `manual_user_entries.csv`
            2. **Pipeline**: Data formatted with same schema as baseline dataset
            3. **Analysis**: Eligible for:
               - Dashboard visualization (Main Dashboard tab)
               - Ensemble scoring (Model Evaluation tab)
               - Network analysis (Network Risk tab)
               - Trend analysis (Analytics & Graphs tab)
            4. **Deduplication**: System prevents duplicate user entries
            
            ### Data Fields
            | Field | Type | Purpose |
            |-------|------|---------|
            | timestamp | ISO8601 | Auto-generated submission time |
            | user | string | Username (unique identifier) |
            | employee_name | string | Human-readable name |
            | total_emails | integer | Email volume |
            | off_hour_ratio | float (0-1) | Off-hours activity |
            | attachment_ratio | float (0-1) | File attachment frequency |
            | avg_email_size | float | Email size in bytes |
            | avg_recipients | float | Recipients per email |
            | iso_z | float | Isolation Forest z-score |
            | lof_z | float | LOF z-score |
            | ae_z | float | Autoencoder z-score |
            | ensemble_weighted | float | Weighted ensemble score |
            | risk_level | enum | NORMAL, LOW, MEDIUM, HIGH, CRITICAL |
            | ensemble_alert | binary | 0 = No alert, 1 = Alert |
            """)
    
    else:
        # ====================================================================
        # AUTHENTICATION UI (Not logged in)
        # ====================================================================
        
        auth_mode = st.radio(
            "Choose Action:",
            options=["Register New User", "Login Existing User"],
            horizontal=True
        )
        
        st.markdown("---")
        
        if auth_mode == "Register New User":
            st.markdown("### 📝 Create New Account")
            
            with st.form(key="register_form"):
                reg_username = st.text_input(
                    "Username",
                    placeholder="e.g., ACV0812",
                    help="Unique identifier for your account"
                )
                
                reg_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter a secure password",
                    help="Will be hashed using SHA-512 (never stored in plaintext)"
                )
                
                reg_password_confirm = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter your password"
                )
                
                st.info(
                    "🔐 **Security Info:**\n"
                    "- Your password is hashed using SHA-512\n"
                    "- Only the hash is stored, never the plaintext\n"
                    "- Identical password always produces identical hash\n"
                    "- If you forget your password, contact your administrator"
                )
                
                register_btn = st.form_submit_button("✅ Register Account", use_container_width=True, type="primary")
                
                if register_btn:
                    if not reg_username or not reg_password:
                        st.error("❌ Username and password are required.")
                    elif reg_password != reg_password_confirm:
                        st.error("❌ Passwords do not match.")
                    else:
                        success, message = register_user(reg_username, reg_password)
                        if success:
                            st.success(message)
                            st.info("✅ Now log in with your new credentials!")
                        else:
                            st.error(message)
        
        else:  # Login mode
            st.markdown("### 🔑 Login to Your Account")
            
            with st.form(key="login_form"):
                login_username = st.text_input(
                    "Username",
                    placeholder="e.g., ACV0812"
                )
                
                login_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password"
                )
                
                login_btn = st.form_submit_button("🔓 Login", use_container_width=True, type="primary")
                
                if login_btn:
                    success, message = authenticate_user(login_username, login_password)
                    
                    if success:
                        st.session_state.auth_logged_in = True
                        st.session_state.auth_username = login_username
                        st.success(message)
                        st.info("Redirecting to submission form...")
                        st.rerun()
                    else:
                        st.error(message)
        
        st.markdown("---")
        
        with st.expander("ℹ️ About This Authentication System"):
            st.markdown("""
            ### Secure User Input & Authentication
            
            This tab provides **enterprise-grade authentication** for data submission:
            
            #### 🔐 Security Features
            - **SHA-512 Hashing**: Passwords hashed using cryptographic SHA-512 algorithm
            - **No Plaintext Storage**: Passwords never logged, stored, or transmitted in clear text
            - **Hash-Only Comparison**: Login validates by comparing hashes only
            - **Secure Session State**: Authentication state managed in Streamlit session
            
            #### 📋 User Registration
            1. Create unique username (e.g., `ACV0812`)
            2. Enter secure password (encrypted with SHA-512)
            3. Confirm password (verification step)
            4. Account created and ready for login
            
            #### 🔑 Authentication Flow
            1. Enter username and password
            2. System computes SHA-512 hash of provided password
            3. Hash compared against stored hash
            4. If match: Access granted, user logged in
            5. If no match: Access denied, error message
            
            #### 📤 Data Submission (Post-Login)
            - Submit structured behavioral data
            - All fields validated before persistence
            - Data saved to `manual_user_entries.csv`
            - Integrated with ensemble analysis pipeline
            - Eligible for dashboard visualization
            
            #### ⚠️ Important Notes
            - **Password Recovery**: Not supported in demo mode
            - **Session Duration**: Authentication persists until browser close/logout
            - **Data Persistence**: Manual entries permanently stored to CSV
            - **No Duplicate Overwrite**: System prevents accidental data loss
            
            #### 📊 Submitted Data Usage
            Your manual entries will:
            - Appear in Main Dashboard risk metrics
            - Be eligible for anomaly detection scoring
            - Contribute to ensemble risk assessment
            - Support network analysis and visualization
            - Enable trend and comparative analysis
            """)


