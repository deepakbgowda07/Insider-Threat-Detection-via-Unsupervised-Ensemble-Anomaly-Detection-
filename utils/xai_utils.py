# ============================================================================
# XAI (EXPLAINABLE AI) UTILITIES MODULE
# ============================================================================

import pandas as pd
import numpy as np


def generate_behavioral_explanation(user_row, df_context):
    """
    Generate comprehensive behavioral explanation for a user
    
    Args:
        user_row (pd.Series): User data row
        df_context (pd.DataFrame): Full dataset for context
        
    Returns:
        str: Comprehensive explanation text
    """
    user_id = user_row['user']
    ensemble_score = user_row['ensemble_score']
    iso_score = user_row['iso_score']
    lof_score = user_row['lof_score']
    ae_score = user_row['ae_score']
    
    explanation = f"### 🔍 Behavioral Analysis for {user_id}\n\n"
    
    # Risk assessment
    if ensemble_score >= 0.8:
        explanation += "#### 🚨 CRITICAL RISK ASSESSMENT\n"
        explanation += f"This user exhibits **significant anomalous behavior** with an ensemble risk score of **{ensemble_score:.3f}**.\n\n"
    elif ensemble_score >= 0.6:
        explanation += "#### ⚠️ HIGH RISK ASSESSMENT\n"
        explanation += f"This user shows **notable anomalous patterns** with an ensemble risk score of **{ensemble_score:.3f}**.\n\n"
    elif ensemble_score >= 0.4:
        explanation += "#### ⚡ MEDIUM RISK ASSESSMENT\n"
        explanation += f"This user exhibits **moderate deviations** from normal behavior with a risk score of **{ensemble_score:.3f}**.\n\n"
    else:
        explanation += "#### ✅ NORMAL BEHAVIOR\n"
        explanation += f"This user's behavior appears **within expected parameters** with a risk score of **{ensemble_score:.3f}**.\n\n"
    
    # Model consensus analysis
    explanation += "#### 📊 Model Consensus\n"
    model_scores = [iso_score, lof_score, ae_score]
    model_names = ["Isolation Forest", "LOF", "Autoencoder"]
    
    consensus = sum(1 for score in model_scores if score >= 0.6)
    
    if consensus == 3:
        explanation += "✓ **All three anomaly detectors concur** - strong evidence of anomalous behavior\n"
    elif consensus == 2:
        explanation += "⚠ **Two detectors flagged anomalies** - moderate evidence of unusual patterns\n"
    else:
        explanation += "○ **Mixed signals from detectors** - isolated anomalies or borderline cases\n"
    
    explanation += "\n**Model Scores:**\n"
    for name, score in zip(model_names, model_scores):
        risk_level = "🔴 HIGH" if score >= 0.6 else "🟡 MEDIUM" if score >= 0.4 else "🟢 NORMAL"
        explanation += f"- {name}: {score:.3f} {risk_level}\n"
    
    # Statistical context
    explanation += f"\n#### 📈 Statistical Context\n"
    mean_score = df_context['ensemble_score'].mean()
    median_score = df_context['ensemble_score'].median()
    percentile = (df_context['ensemble_score'] < ensemble_score).sum() / len(df_context) * 100
    
    explanation += f"- **Ensemble Score Mean:** {mean_score:.3f}\n"
    explanation += f"- **This User's Score:** {ensemble_score:.3f} ({percentile:.1f}th percentile)\n"
    
    # Behavioral features (simplified)
    explanation += f"\n#### 🔎 Key Observations\n"
    
    num_features = len(user_row)
    high_variance_features = []
    
    # Approximate feature analysis
    if iso_score >= 0.7:
        high_variance_features.append("unusual data patterns")
    if lof_score >= 0.7:
        high_variance_features.append("isolated behavior clusters")
    if ae_score >= 0.7:
        high_variance_features.append("reconstructed data divergence")
    
    if high_variance_features:
        explanation += "- " + ", ".join(high_variance_features) + "\n"
    
    explanation += f"- User represents **{percentile:.1f}% of population** risk distribution\n"
    
    # Recommendations
    explanation += f"\n#### 💡 Recommendations\n"
    if ensemble_score >= 0.8:
        explanation += "1. **Immediate Investigation:** Conduct urgent forensic analysis\n"
        explanation += "2. **Access Review:** Verify all recent access logs and activities\n"
        explanation += "3. **Escalation:** Alert security team immediately\n"
    elif ensemble_score >= 0.6:
        explanation += "1. **Priority Investigation:** Schedule detailed review within 24 hours\n"
        explanation += "2. **Monitoring:** Increase monitoring frequency\n"
        explanation += "3. **Documentation:** Prepare incident report\n"
    elif ensemble_score >= 0.4:
        explanation += "1. **Standard Review:** Include in regular monitoring cycle\n"
        explanation += "2. **Tracking:** Monitor for trend changes\n"
    else:
        explanation += "1. **Routine Monitoring:** Continue standard security monitoring\n"
    
    return explanation


def generate_comparison_insight(user_score, df_context, metric="ensemble_score"):
    """
    Generate insight text comparing user to population
    
    Args:
        user_score (float): User's risk score
        df_context (pd.DataFrame): Full dataset
        metric (str): Column name to compare
        
    Returns:
        str: Comparison insight text
    """
    percentile = (df_context[metric] < user_score).sum() / len(df_context) * 100
    
    if percentile >= 95:
        return f"⚠️ User is in **TOP 5%** highest risk - {percentile:.1f}th percentile"
    elif percentile >= 75:
        return f"⚡ User is in **TOP 25%** risk group - {percentile:.1f}th percentile"
    elif percentile >= 50:
        return f"📊 User is in **upper-middle** risk distribution - {percentile:.1f}th percentile"
    else:
        return f"✅ User is in **lower-risk** population - {percentile:.1f}th percentile"
