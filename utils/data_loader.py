# ============================================================================
# DATA LOADING & PREPROCESSING MODULE
# ============================================================================

import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


@st.cache_data
def load_and_preprocess_data():
    """
    Load CSV and apply ML preprocessing (ensemble, normalization, etc.)
    Returns fully preprocessed DataFrame ready for analysis.
    """
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
