# ============================================================================
# METRICS & EVALUATION MODULE
# ============================================================================

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def compute_proxy_metrics(df):
    """
    Compute proxy evaluation metrics for unsupervised system
    
    Args:
        df (pd.DataFrame): Data with ensemble scores and pseudo-labels
        
    Returns:
        dict: Computed metrics
    """
    metrics = {}
    
    try:
        if df['pseudo_label_strict'].nunique() > 1:
            # Full dataset ROC-AUC
            metrics['roc_full'] = roc_auc_score(
                df['pseudo_label_strict'], 
                df['ensemble_weighted']
            )
            
            # Tail 30% ROC-AUC
            tail_df = df[df['ensemble_weighted'] > df['ensemble_weighted'].quantile(0.70)]
            if tail_df['pseudo_label_strict'].nunique() > 1:
                metrics['roc_tail'] = roc_auc_score(
                    tail_df['pseudo_label_strict'], 
                    tail_df['ensemble_weighted']
                )
            else:
                metrics['roc_tail'] = np.nan
        else:
            metrics['roc_full'] = np.nan
            metrics['roc_tail'] = np.nan
    except Exception as e:
        metrics['roc_full'] = np.nan
        metrics['roc_tail'] = np.nan
    
    # False Positive Rate
    actual_normal = df[df['pseudo_label_strict'] == 0]
    false_positives = actual_normal[actual_normal['ensemble_alert'] == 1]
    metrics['fpr'] = len(false_positives) / len(actual_normal) if len(actual_normal) > 0 else 0
    
    # Trustworthiness (proxy)
    metrics['trustworthiness'] = max(0, 1 - (metrics['fpr'] / 2))
    
    # Alert threshold
    metrics['alert_threshold'] = df['ensemble_weighted'].quantile(0.90)
    
    # Alert count
    metrics['alerts_count'] = df['ensemble_alert'].sum()
    
    # Alerts matching pseudo-positives
    metrics['alerts_tp'] = len(df[(df['ensemble_alert'] == 1) & (df['pseudo_label_strict'] == 1)])
    
    # Score statistics
    metrics['score_mean'] = df['ensemble_weighted'].mean()
    metrics['score_std'] = df['ensemble_weighted'].std()
    metrics['score_median'] = df['ensemble_weighted'].median()
    
    return metrics


def get_metrics_dataframe(df):
    """
    Get metrics as formatted DataFrame for display
    
    Args:
        df (pd.DataFrame): Data with ensemble scores
        
    Returns:
        pd.DataFrame: Formatted metrics table
    """
    metrics = compute_proxy_metrics(df)
    
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
            f"{metrics['roc_full']:.3f}",
            f"{metrics['roc_tail']:.3f}",
            f"{metrics['alert_threshold']:.3f}",
            f"{metrics['alerts_count']}",
            f"{metrics['alerts_tp']}",
            f"{metrics['fpr']:.2%}",
            "3 (IF, LOF, AE)",
            f"{metrics['score_std']:.3f}"
        ]
    })
    
    return metrics_df
