# Insider Threat Detection Dashboard

## Overview

A **production-grade, SOC-style Streamlit dashboard** for unsupervised insider threat detection using ensemble-based anomaly scoring. This system is designed for research demos, internal monitoring, and pilot deployments.

**Key Features:**
- ✅ Dark theme, professional SOC-style UI
- ✅ Ensemble of 3 independent anomaly detectors (Isolation Forest, LOF, Autoencoder)
- ✅ Explainable AI (XAI) for every user alert
- ✅ Multi-tab architecture (6 main sections)
- ✅ Real-time filtering and dynamic updates
- ✅ Research-grade evaluation metrics (proxy ROC-AUC, FPR, trustworthiness)
- ✅ Clean, modular, well-documented Python code

---

## Architecture & Features

### Tab 1: Main Dashboard
**The entry point for analysts.**

**Components:**
- **KPI Cards**: Total users, counts by risk level (CRITICAL, HIGH, MEDIUM, NORMAL)
- **Risk Distribution Bar**: Horizontal stacked bar showing proportion of each risk level
- **User Risk Rankings Table**: 
  - Sorted by ensemble score (descending)
  - Color-coded by risk level
  - Shows individual model scores (ISO Forest, LOF, Autoencoder)
  - Supports sorting and filtering

**Sidebar:**
- Multi-select risk level filter (CRITICAL, HIGH, MEDIUM, NORMAL)
- Live statistics (total users, alerted users, filtered users)
- Dynamic updates on filter change

---

### Tab 2: Analytics & Graphs
**Research-grade visual analytics.**

**Graphs:**
1. **Anomaly Score Distribution**: Histogram with alert threshold marked
2. **Risk-wise Score Distribution**: Violin plot by risk level
3. **Model Contribution**: Stacked bar showing ensemble weights (40% LOF, 30% IF, 30% AE)
4. **Reconstruction Error Analysis**: Mean error per risk level with confidence bands
5. **Model Performance (Proxy ROC-AUC)**: 
   - Comparison of individual models vs. ensemble
   - Clearly labeled as "proxy" (not ground truth)
   - Evaluated against heuristic pseudo-labels

---

### Tab 3: User Deep Dive & Explainability
**Detailed XAI for individual users.**

**Components:**
- **User Selection Dropdown**: Choose any user for analysis
- **Risk Summary Cards**: Risk level, ensemble score, alert status, percentile
- **Base Model Decisions**: Individual flagging decisions from IF, LOF, AE
- **Behavioral Indicators Table**:
  - Feature name
  - User's value
  - Peer 75th percentile
  - Interpretation (⚠️ Unusual / Normal)
- **Natural Language Explanation**: 
  - Why user was flagged (plain English)
  - Statistical comparisons with peers
- **Recommended Analyst Actions**:
  - Context-aware recommendations (CRITICAL vs HIGH vs MEDIUM)
  - Investigative steps and timelines
- **Raw Feature JSON**: Collapsible section for detailed feature inspection

---

### Tab 4: Network Risk Visualization
**Spatial analysis of anomalies.**

**Components:**
- **PCA Projection Scatter**: 
  - 2D visualization using Principal Component Analysis
  - Node size = ensemble anomaly score
  - Color = risk level
  - Shows behavioral clustering
- **Spatial Statistics**:
  - Anomaly concentration (% of users above threshold)
  - Risk dispersion (standard deviation of scores)

---

### Tab 5: Model Evaluation
**Proxy metrics for system assessment.**

**Metrics:**
- **Proxy ROC-AUC (Full Dataset)**: All users
- **Proxy ROC-AUC (Tail 30%)**: Top anomalies only
- **False Positive Rate**: % of "normal" users that were alerted
- **Trustworthiness Score**: System reliability proxy

**Detailed Table:**
- Alert threshold (90th percentile)
- Number of alerted users
- Alerted users vs. pseudo-positives
- Ensemble composition
- Score variance

**Metric Explanations (Expandable):**
- What is proxy ROC-AUC?
- What is false positive rate?
- Why is ROC-AUC marked as "proxy"?
- What is trustworthiness?

---

### Tab 6: How Does This Work?
**Non-technical explanation guide.**

**Sections:**
- What is insider threat? (types, examples)
- Why unsupervised learning? (lack of labeled data)
- How the ensemble system works (3 detectors, voting mechanism)
- What features are analyzed? (off-hour, attachments, email size, etc.)
- Risk levels explained (CRITICAL, HIGH, MEDIUM, NORMAL)
- How to use the dashboard (6-step guide)
- Limitations & disclaimers (important caveats)
- Technical references (papers, citations)

---

## Data Flow & Preprocessing

### Input CSV Structure
**Required columns:**
- `user`: User identifier
- `employee_name`: Human-readable name
- `risk_level`: Ground truth or heuristic risk label (CRITICAL, HIGH, MEDIUM, NORMAL)
- `iso_score`: Isolation Forest anomaly score
- `lof_score`: Local Outlier Factor score
- `ae_score`: Autoencoder reconstruction error
- `iso_anomaly`, `lof_anomaly`, `ae_anomaly`: Binary flags (0/1)
- `ensemble_score`: Pre-computed ensemble flag (optional)
- Behavioral features: `off_hour_ratio`, `attachment_ratio`, `avg_email_size`, `avg_recipients`, `total_emails`, `avg_content_length`, etc.

### Preprocessing Pipeline
```python
1. Z-score normalization of each model's scores (iso_z, lof_z, ae_z)
2. Weighted ensemble: 0.4*lof_z + 0.3*iso_z + 0.3*ae_z
3. Reconstruction error proxy: |ae_score|
4. Alert threshold: 90th percentile of ensemble score
5. Pseudo-label generation (heuristic for evaluation):
   - off_hour_ratio > 30% OR
   - attachment_ratio > 20% OR
   - avg_email_size > 90th percentile
   - (Score 2+ criteria as "pseudo-positive")
```

---

## Running the Dashboard

### Prerequisites
```bash
pip install streamlit pandas numpy scikit-learn matplotlib seaborn
```

### Launch
```bash
cd c:\Users\Kanna\OneDrive\Desktop\PROJECT_FINAL
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

---

## Key Design Decisions

### 1. **Dark Theme (SOC-Style)**
- **Color Palette**: 
  - CRITICAL: #ff4444 (red)
  - HIGH: #ff9800 (orange)
  - MEDIUM: #fbc02d (yellow)
  - NORMAL: #66bb6a (green)
- **Background**: Dark (#0a0e27) for reduced eye strain in 24/7 SOC environments
- **Text**: Light gray (#e0e0e0) for accessibility

### 2. **Ensemble Weights (40/30/30)**
- **LOF (40%)**: Most sensitive to local density deviations; catches context-dependent anomalies
- **Isolation Forest (30%)**: Fast, interpretable; good for global outliers
- **Autoencoder (30%)**: Neural network captures non-linear patterns
- **Rationale**: Diversity prevents single-model failures; weights tuned for complementarity

### 3. **Alert Threshold (90th Percentile)**
- Conservative cutoff to minimize false positives
- Approximately 20 alerts from 200 users (10%)
- Can be tuned based on analyst workload and risk tolerance

### 4. **Proxy Metrics Over False Claims**
- NO claim of "X% accuracy" (unsupervised systems lack ground truth)
- Pseudo-labels derived from heuristics (multi-criteria: off-hour + attachments + size)
- Metrics transparently labeled as "proxy"
- Each metric has expandable explanation

### 5. **XAI-First Design**
- Every user gets narrative explanation (not just a score)
- Behavioral indicator table shows peer comparisons
- Recommended actions are context-aware, not generic
- Model decisions decomposed (IF vs LOF vs AE shown separately)

---

## Explainability Features

### Plain-English Generation
For each user, the system explains:
1. **Ensemble Score Magnitude**: How many sigmas above/below mean?
2. **Off-Hour Activity**: Ratio compared to peers (e.g., "2x higher than median")
3. **Attachment Behavior**: % of emails with attachments (flagged if >1.5x peer median)
4. **Email Size**: Average message size (flagged if >1.5x peer median)
5. **Communication Isolation**: Fewer recipients than typical for role?

### Model Contribution Visibility
- Each base model's decision shown (FLAGGED / Normal)
- Individual z-scores displayed alongside ensemble score
- Helps analysts understand consensus vs. dissent among models

### Behavior Table
- Quantitative comparison: User Value vs. Peer 75th Percentile
- Visual interpretation: ⚠️ Unusual OR Normal
- Makes it obvious which behaviors drive the alert

---

## Limitations & Important Caveats

### Unsupervised (No Ground Truth)
- System trained WITHOUT confirmed insider threat examples
- Cannot claim supervised accuracy metrics
- Proxy ROC-AUC is heuristic-based, not validated

### Concept Drift
- User behavior changes over time (new role, promotion, new project)
- System may flag legitimate behavioral shifts as anomalies
- Requires periodic retraining and threshold adjustment

### False Positives
- Conservative ensemble may flag legitimate users
- Analysts MUST investigate every alert contextually
- False positive rate should be monitored and tuned

### Dependency on Feature Quality
- Assumes accurate email metadata (timestamps, recipients, sizes)
- Garbage data → garbage anomalies
- Feature engineering matters for performance

---

## Deployment Recommendations

### Pilot Phase (First 30 Days)
1. Monitor CRITICAL alerts daily
2. Document all alerts and investigation outcomes
3. Collect feedback from security analysts
4. Calculate actual false positive rate
5. Adjust thresholds if needed (e.g., use 85th vs. 90th percentile)

### Integration
1. Feed dashboard outputs to SIEM/ticketing system
2. Combine with other signals (endpoint, network, logs)
3. Set up alerts for CRITICAL users (email to SOC)
4. Create investigation playbooks for each risk level

### Maintenance
1. **Weekly**: Review top 5 alerts, validate explanations
2. **Monthly**: Retrain ensemble models on latest data
3. **Quarterly**: Recalibrate thresholds based on outcomes
4. **Annually**: Audit system for bias, drift, and fairness

---

## Code Structure

### Main Sections
1. **Page Config & Theme**: Streamlit setup, dark mode CSS
2. **Data Loading & Preprocessing**: CSV load, feature engineering, ensemble scoring
3. **Utility Functions**: Risk color mapping, explanation generation, visualization helpers
4. **Sidebar**: Risk filter, dataset statistics
5. **6 Tabs**: Each with full content and interactivity

### Key Functions
- `load_and_preprocess_data()`: One-time data load with caching
- `risk_to_color()`: Maps risk level to HEX color
- `get_risk_description()`: Short risk summary text
- `render_risk_summary_bar()`: Horizontal stacked bar chart (custom HTML)
- `generate_behavioral_explanation()`: Natural language XAI generation

### No External ML Training
- **Ensemble already computed** in input CSV
- Dashboard is **purely visualization + explainability**
- No retraining; uses pre-computed scores from backend ML system

---

## Future Enhancements

### Short-term
- [ ] User feedback loop (mark false positives/negatives)
- [ ] Time-series visualization (score trends over weeks)
- [ ] Peer group comparison (what does a similar role look like?)
- [ ] Alert export (CSV, PDF reports for stakeholders)

### Medium-term
- [ ] Integration with email/file servers for live monitoring
- [ ] Automated threshold tuning based on outcomes
- [ ] Role-based alert clustering (group anomalies by department)
- [ ] Collaborative investigation (comments, tags, case management)

### Long-term
- [ ] Retraining pipeline (daily/weekly model updates)
- [ ] Active learning (query most uncertain cases)
- [ ] Cross-organization benchmarking
- [ ] Regulatory compliance reporting (HIPAA, SOX, etc.)

---

## Contact & Support

For questions or issues:
1. Check the "How Does This Work?" tab for usage guidance
2. Review metric explanations (expandable sections in "Model Evaluation")
3. Consult the Technical References section for academic sources
4. Validate assumptions with your security/data science team

---

**Built for**: Research-grade insider threat detection  
**Status**: Production-ready for pilot deployments  
**Last Updated**: January 2026
"# Insider-Threat-Detection-via-Unsupervised-Ensemble-Anomaly-Detection-" 
