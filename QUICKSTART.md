# Quick Start Guide

## 30-Second Setup

```bash
# Navigate to project folder
cd c:\Users\Kanna\OneDrive\Desktop\PROJECT_FINAL

# Ensure dependencies installed
pip install streamlit pandas numpy scikit-learn matplotlib seaborn

# Launch dashboard
streamlit run app.py
```

Dashboard opens at: **http://localhost:8501**

---

## First Time User? Start Here

### 1. **Main Dashboard Tab** (First Screen)
- See overall risk distribution (CRITICAL, HIGH, MEDIUM, NORMAL)
- View top 20 at-risk users sorted by anomaly score
- Use sidebar filter to show only CRITICAL/HIGH alerts
- **Action**: Note the most concerning users

### 2. **User Deep Dive Tab**
- Click a user from the main table or select from dropdown
- Read the plain-English explanation: **"Why This User Was Flagged"**
- Check **"Key Behavioral Indicators"** table to see which behaviors triggered the alert
- Review **"Recommended Analyst Actions"** for investigation steps
- **Action**: Decide if alert warrants investigation

### 3. **Analytics & Graphs Tab**
- Understand score distributions and model performance
- See how the 3 anomaly detectors compare
- Check false positive rate and proxy ROC-AUC
- **Action**: Gain confidence in system decisions

### 4. **How Does This Work? Tab**
- Read non-technical explanation of insider threat
- Learn what unsupervised learning means
- Understand limitations and important caveats
- **Action**: Get context for management/stakeholder briefings

---

## Key Takeaways

### Green Flags ✅
- User flagged by multiple models (ensemble agreement)
- Clear behavioral deviation from peers (table shows this)
- Explanation makes sense contextually
- Simple, isolated anomalies (not borderline)

### Red Flags ⚠️
- Flagged by only 1 model (ensemble dissent)
- Borderline scores near threshold
- Behavioral explanation applies to many users in same role
- Recent hire or role change not yet reflected in system

---

## Common Workflows

### "I need to brief my manager on top risks"
1. Go to **Main Dashboard**
2. Note the 5-10 CRITICAL users
3. Click one, go to **User Deep Dive**
4. Copy the explanation and analyst actions
5. Use data from **Model Evaluation** tab to explain metrics

### "Is this really an insider threat?"
1. Go to **User Deep Dive**, select the user
2. Read the explanation section carefully
3. Check if there's legitimate business reason:
   - New employee (still ramping up)
   - Recent promotion (new tools/contacts)
   - Special project (unusual but approved)
   - Audit/quarter-end (normal spike)
4. If unsure, escalate to manager for context

### "I want to understand the system"
1. Start with **How Does This Work?** tab
2. Go to **Analytics & Graphs** to see distributions
3. Check **Model Evaluation** for transparency
4. Read expandable metric explanations

---

## Important Reminders

⚠️ **This is a screening tool, not a verdict**
- Always verify alerts with contextual investigation
- Don't take anomaly scores as proof of guilt
- Combine with other signals (access logs, network, behavioral interviews)

⚠️ **Context matters**
- New employees naturally score higher
- Legitimate projects can cause unusual behavior
- Business cycles (quarter-end, audits) create spikes

⚠️ **These are proxy metrics**
- No ground truth labels in unsupervised learning
- ROC-AUC is heuristic-based, not validated
- False positive rate varies by threshold choice

---

## FAQ

**Q: What does "Proxy ROC-AUC" mean?**
A: Without confirmed insider threats in your data, we can't compute real ROC-AUC. Instead, we evaluate against behavioral heuristics (off-hour + attachments + size). It's a proxy for system quality, not a claim of accuracy.

**Q: Why is my role's new employee flagged as HIGH risk?**
A: New employees haven't learned the role yet. They naturally have unusual communication patterns. Check the reason—if it's just "lower activity," it's likely false positive. Revisit in 30-60 days.

**Q: Can I tune the alert threshold?**
A: Yes, but it's a tradeoff. Lower threshold = more alerts but catch more threats. Higher threshold = fewer alerts but miss some. Recommendation: start at 90th percentile, adjust after 2 weeks of data.

**Q: How often should I retrain the models?**
A: The pre-computed ensemble in your CSV is static. To retrain, you'd need the ML backend to re-run. Recommend monthly updates as users' roles and behavior evolve.

**Q: Is this GDPR/HIPAA compliant?**
A: This tool itself doesn't store PII beyond necessary metadata. Ensure your deployment handles consent, data retention, and investigative fairness. Always combine with HR/legal review.

---

## Support & Troubleshooting

### Dashboard won't load
```bash
# Check Streamlit is installed
pip show streamlit

# Try running with verbose logging
streamlit run app.py --logger.level=debug
```

### CSV not found
- Ensure `final_risk_output (1).csv` is in same folder as `app.py`
- Check file name matches exactly (case-sensitive on Linux)

### Charts not rendering
- Check matplotlib is installed: `pip install matplotlib seaborn`
- Try refreshing the browser (Ctrl+F5)

### Filters not updating
- Clear browser cache or use incognito mode
- Reload Streamlit: press 'R' in the Streamlit console

---

## Next Steps

1. ✅ Launch dashboard (see 30-second setup)
2. ✅ Explore each tab (spend 5 min on each)
3. ✅ Deep-dive on 1-2 users from your dataset
4. ✅ Read "How Does This Work?" tab completely
5. ✅ Plan investigation workflow for CRITICAL alerts
6. ✅ Integrate into your SOC process (ticketing, escalation, etc.)

---

Good luck with your insider threat program! 🔒
