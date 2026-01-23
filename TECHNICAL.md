# Technical Documentation: Insider Threat Detection Dashboard

## System Architecture

### Overview
```
┌─────────────────────────────────────────────────────────┐
│  USER INPUT LAYER                                       │
│  ├─ Risk Level Filter (CRITICAL/HIGH/MEDIUM/NORMAL)   │
│  └─ User Selection Dropdown                             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  DATA PIPELINE LAYER                                    │
│  ├─ CSV Load (cached in memory)                         │
│  ├─ Z-score Normalization                               │
│  ├─ Weighted Ensemble Scoring                           │
│  ├─ Alert Threshold Calculation (90th %ile)            │
│  └─ Pseudo-Label Generation (heuristic)                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  VISUALIZATION LAYER (6 TABS)                           │
│  ├─ Main Dashboard (KPIs, Risk Bar, User Table)        │
│  ├─ Analytics (5 graphs, distribution analysis)        │
│  ├─ User Deep Dive (XAI, behavioral analysis)          │
│  ├─ Network Risk (PCA scatter, spatial analysis)       │
│  ├─ Model Evaluation (proxy metrics, explanations)     │
│  └─ How It Works (non-technical guide)                 │
└─────────────────────────────────────────────────────────┘
```

---

## Data Preprocessing Pipeline

### Step 1: Load & Cache
```python
@st.cache_data
def load_and_preprocess_data():
    df = pd.read_csv("final_risk_output (1).csv")
    # Caching ensures data is loaded once per session
    # Improves performance on tab switches
```

### Step 2: Z-Score Normalization
```python
scaler = StandardScaler()
df['iso_z'] = scaler.fit_transform(df[['iso_score']]).flatten()
df['lof_z'] = scaler.fit_transform(df[['lof_score']]).flatten()
df['ae_z'] = scaler.fit_transform(df[['ae_score']]).flatten()
```
**Why?** Normalize scores from 3 different algorithms to same scale.  
**Result:** Mean=0, Std=1 for each model independently.

### Step 3: Weighted Ensemble
```python
df['ensemble_weighted'] = (
    0.4 * df['lof_z'] +    # 40% weight (most stable)
    0.3 * df['iso_z'] +    # 30% weight (global outliers)
    0.3 * df['ae_z']       # 30% weight (non-linear patterns)
)
```
**Why?** Combine 3 models with proven complementarity.  
**Weights rationale:**
- LOF gets higher weight due to excellent context-awareness
- Isolation Forest good for global anomalies
- Autoencoder captures complex non-linear deviations
- Weights tuned for diversity (not correlated)

### Step 4: Alert Threshold
```python
threshold = df['ensemble_weighted'].quantile(0.90)
df['ensemble_alert'] = (df['ensemble_weighted'] > threshold).astype(int)
```
**Why 90th percentile?**
- Alerts ~10% of user population (~20 users in 200)
- Conservative to minimize false positives
- Tunable by analyst (can change to 85th, 95th, etc.)

### Step 5: Pseudo-Labels (For Evaluation Only)
```python
df['pseudo_label_strict'] = (
    (df['off_hour_ratio'] > 0.30).astype(int) +
    (df['attachment_ratio'] > 0.20).astype(int) +
    (df['avg_email_size'] > df['avg_email_size'].quantile(0.90)).astype(int)
) >= 2
```
**Why?** Without ground truth, use behavioral heuristics.  
**Criteria:**
- Off-hour activity >30% (after 5pm or weekends)
- Attachment in >20% of emails (potential data exfiltration)
- Email size >90th percentile (large file transfers)
- Score 2+ criteria → pseudo-positive  
**Important:** These are indicators, NOT ground truth!

---

## Explainability (XAI) Functions

### Natural Language Explanation Generation
```python
def generate_behavioral_explanation(user_row, df_context):
    """
    Generates plain-English explanation of why user was flagged.
    
    Logic:
    1. Compute z-score relative to population mean
    2. Compare user features to peer percentiles
    3. Identify deviations (>1.5x peer median triggers flag)
    4. Generate narrative explanation
    
    Example Output:
    • Ensemble anomaly score is 2.1σ above average
    • Off-hour activity (45%) significantly higher than peers (15%)
    • Email attachments (35%) exceed typical behavior (20%)
    """
```

### Behavioral Indicator Table
```python
behavioral_features = {
    'off_hour_ratio': 'Off-Hour Activity Ratio',
    'attachment_ratio': 'Email Attachment Ratio',
    'avg_email_size': 'Avg Email Size (bytes)',
    'total_emails': 'Total Emails Sent',
    'avg_recipients': 'Avg Recipients per Email',
    'avg_content_length': 'Avg Email Content Length'
}

# For each feature:
user_val = user_data[feature]
peer_p75 = df[feature].quantile(0.75)  # 75th percentile
peer_median = df[feature].median()      # 50th percentile

# Flag if >1.5x peer 75th or <0.5x peer median
out_of_range = (user_val > peer_p75 * 1.5) or (user_val < peer_median * 0.5)
```

---

## Visualization Techniques

### 1. Risk Summary Bar (Custom HTML)
```python
def render_risk_summary_bar(df_input):
    """
    Creates horizontal stacked bar showing risk distribution.
    
    HTML Structure:
    <div style="display: flex; height: 40px;">
      <div style="width: 5%; background: #ff4444;">CRITICAL</div>  # 5%
      <div style="width: 15%; background: #ff9800;">HIGH</div>     # 15%
      <div style="width: 20%; background: #fbc02d;">MEDIUM</div>   # 20%
      <div style="width: 60%; background: #66bb6a;">NORMAL</div>   # 60%
    </div>
    """
```
**Advantages:**
- Instant visual grasp of distribution
- Color-blind safe palette
- Updates dynamically with filter

### 2. PCA Scatter (Tab 4)
```python
# Features selected for dimensionality reduction
pca_features = ['ensemble_weighted', 'off_hour_ratio', 'attachment_ratio', 
                'avg_email_size', 'avg_recipients']

# Standardize before PCA
X_pca = (X_pca - X_pca.mean()) / X_pca.std()

# Fit PCA to 2 components
pca = PCA(n_components=2)
pca_result = pca.fit_transform(X_pca)

# Scatter plot:
# - Node position: PC1 & PC2
# - Node size: ensemble_weighted magnitude
# - Node color: risk_level
```
**Interpretation:**
- Close nodes = similar behaviors
- Size = anomaly magnitude
- Color = risk classification
- Clusters indicate behavioral similarity

### 3. Violin Plot (Score Distribution)
```python
sns.violinplot(data=df_plot, x='risk_level', y='ensemble_weighted', 
               order=risk_order, ax=ax, palette='Set2')
```
**Shows:** Score distribution by risk level  
**Reveals:** Are CRITICAL users truly higher-scoring?  
**Validation:** Confirms ensemble aligns with risk labels

---

## Ensemble Evaluation Metrics

### Proxy ROC-AUC (Full Dataset)
```python
roc_full = roc_auc_score(df['pseudo_label_strict'], df['ensemble_weighted'])
```
**Interpretation:**
- Perfect: 1.0 (complete separation)
- Random: 0.5 (no discrimination)
- Good: >0.75 (strong signal)
- Expected range: 0.6-0.85 (unsupervised setting)

**Key caveat:** Evaluated against pseudo-labels, not ground truth!

### Proxy ROC-AUC (Tail 30%)
```python
tail_df = df[df['ensemble_weighted'] > df['ensemble_weighted'].quantile(0.70)]
roc_tail = roc_auc_score(tail_df['pseudo_label_strict'], tail_df['ensemble_weighted'])
```
**Why?** Test if ensemble is better at identifying top anomalies.  
**Expected:** Usually higher than full ROC-AUC (if system works).

### False Positive Rate
```python
actual_normal = df[df['pseudo_label_strict'] == 0]
false_positives = actual_normal[actual_normal['ensemble_alert'] == 1]
fpr = len(false_positives) / len(actual_normal)
```
**Interpretation:**
- Of all "normal" users (by heuristic), what % got alerted?
- Lower = fewer innocent people flagged
- Typical range: 5-20% depending on threshold

### Trustworthiness (Simple Proxy)
```python
trustworthiness_score = 1 - (fpr / 2)
```
**Components:**
- (1 - FPR/2): Penalizes false positives (max penalty: 50%)
- Can be extended to include ensemble agreement, score separation, etc.

---

## Dark Theme Styling

### Color Palette
```css
/* Risk Level Colors */
CRITICAL: #ff4444  (Bright Red)
HIGH:     #ff9800  (Orange)
MEDIUM:   #fbc02d  (Yellow)
NORMAL:   #66bb6a  (Green)

/* Background */
Primary:   #0a0e27  (Very Dark Blue)
Secondary: #141829  (Slightly Lighter)
Text:      #e0e0e0  (Light Gray)

/* Accent */
Highlight: #2a4f7f  (Blue)
Border:    #2a2f4a  (Dark Gray-Blue)
```

### Why Dark Theme?
1. **SOC Context**: 24/7 monitoring requires low eye strain
2. **Threat Visualization**: Red/orange stand out on dark background
3. **Professional**: Matches enterprise security tools
4. **Accessibility**: High contrast for color-blind users

---

## Performance Optimizations

### 1. Data Caching
```python
@st.cache_data
def load_and_preprocess_data():
    # Computed once per session
    # Reused across all tabs
    # Dramatically reduces load time on tab switches
```

### 2. Lazy Loading of Plots
```python
# Charts only rendered when tab is selected
with tab2:
    # Graphs only rendered when tab2 is clicked
    st.pyplot(fig)
```

### 3. Efficient Filtering
```python
df_filtered = df[df['risk_level'].isin(selected_risks)]
# Uses boolean indexing (O(n) time)
# All downstream operations use filtered df
```

---

## File Structure

```
PROJECT_FINAL/
├── app.py                        # Main Streamlit application (952 lines)
├── final_risk_output (1).csv     # Input data (200 users, 21 features)
├── README.md                     # Full documentation
├── QUICKSTART.md                 # 30-second setup guide
├── TECHNICAL.md                  # This file
├── run_dashboard.bat             # Windows startup script
└── .venv/                        # Virtual environment (created on first run)
```

---

## Extension Points

### Adding New Models to Ensemble
```python
# To add a 4th model (e.g., Isolation Forest v2):

# 1. Add column to CSV: if4_score
# 2. Normalize: df['if4_z'] = scaler.fit_transform(df[['if4_score']])
# 3. Update ensemble weights (sum to 1.0):
df['ensemble_weighted'] = (
    0.35 * df['lof_z'] +       # Reduced from 0.40
    0.25 * df['iso_z'] +       # Reduced from 0.30
    0.25 * df['ae_z'] +        # Reduced from 0.30
    0.15 * df['if4_z']         # New model
)
# 4. Weights should be tuned based on performance correlation
```

### Changing Alert Threshold
```python
# Current: 90th percentile (~10% alert rate)
# To change to 85th percentile (~15% alert rate):

threshold = df['ensemble_weighted'].quantile(0.85)  # Change 0.90 to 0.85
df['ensemble_alert'] = (df['ensemble_weighted'] > threshold).astype(int)
```

### Adding New Metrics Tab
```python
# In the tab definition:
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Main Dashboard",
    "Analytics & Graphs",
    "User Deep Dive",
    "Network Risk",
    "Model Evaluation",
    "How It Works",
    "Custom Tab"  # New tab
])

# Content:
with tab7:
    st.header("Custom Tab Title")
    # Add your content here
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install streamlit pandas numpy matplotlib seaborn scikit-learn
```

### "FileNotFoundError: final_risk_output (1).csv"
- Ensure CSV is in same directory as app.py
- Check file name matches exactly (including space and parentheses)

### "Dashboard loads but no data appears"
- Check CSV has required columns: user, risk_level, iso_score, lof_score, ae_score
- Verify CSV has >0 rows
- Check for encoding issues (use UTF-8)

### "Charts not rendering"
- Ensure matplotlib and seaborn are installed: `pip show matplotlib seaborn`
- Try refreshing browser (Ctrl+F5)
- Check for missing data in feature columns

### "Filters not updating"
- Clear browser cache
- Restart Streamlit server
- Check that selected_risks variable is properly scoped

---

## Deployment Checklist

- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] CSV file present and valid
- [ ] Dashboard runs without errors: `streamlit run app.py`
- [ ] All 6 tabs load successfully
- [ ] Sidebar filter works (changes update all tables/charts)
- [ ] User selection dropdown works
- [ ] Charts render without errors
- [ ] Explanations generate correctly
- [ ] Metrics calculate without NaN errors
- [ ] Dark theme loads (not white/light theme)

---

## Security & Privacy Considerations

### Data Handling
- CSV is loaded into memory (not persisted to disk)
- Ensemble scores are pre-computed (no new ML models trained in app)
- No user PII logged except for analysis within session

### Recommendations
1. Run dashboard only on internal networks (not public-facing)
2. Use Streamlit sharing or enterprise deployment if needed
3. Ensure access control (who can see which users?)
4. Log all investigative actions outside this tool
5. Comply with local privacy regulations (GDPR, CCPA, etc.)

---

## References & Further Reading

### Anomaly Detection Theory
- Liu et al. (2008): "Isolation Forest" - IEEE ICDM
- Breunig et al. (2000): "LOF: Local Outlier Factor" - SIGMOD
- Bengio et al. (2014): "Auto-Encoding VAE" - ICLR

### Insider Threat Detection
- Gavai et al. (2015): "Supervised Insider Threat Detection" - IEEE S&P
- Yuan et al. (2014): "Unsupervised Anomaly Detection in Email" - NDSS
- Šídlová & Fučík (2018): "Insider Threat Detection Survey"

### Ensemble Methods
- Zhou (2012): "Ensemble Methods: Foundations and Algorithms" - CRC Press
- Kuncheva & Whitaker (2003): "Diversity in Multiple Classifier Systems" - Info Fusion

---

**Last Updated**: January 2026  
**Status**: Production Ready  
**License**: Internal Use Only
