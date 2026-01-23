# 🚀 Quick Start: Secure User Input (Preview-Before-Save)

## 30-Second Overview

The "Secure User Input" tab now works like this:

```
1. Register/Login  →  2. Fill Form  →  3. Preview  →  4. Save (Optional)
```

**Key: Data does NOT save automatically. You must explicitly click "💾 Save Entry"**

---

## ⚡ Fast Workflow

### For First-Time Users

```bash
# Step 1: Register
Tab: "Secure User Input"
Radio: "Register New User"
├─ Username: ACV0812
├─ Password: SecurePass123!
├─ Confirm:  SecurePass123!
└─ Button:   ✅ Register Account

# Step 2: Login
Radio: "Login Existing User"
├─ Username: ACV0812
├─ Password: SecurePass123!
└─ Button:   🔓 Login

# Step 3: Fill Form
├─ Employee Name: Alden Caesar Velez
├─ Total Emails: 35
├─ Off-Hour Ratio: 0.0857
├─ Attachment Ratio: 0.2571
├─ Avg Email Size: 30407.23
├─ Avg Recipients: 2.97
├─ ISO Z-Score: -0.161
├─ LOF Z-Score: -0.346
├─ Autoencoder Z-Score: -0.561
├─ Ensemble Score: -0.355
├─ Risk Level: NORMAL
└─ Alert Flag: 0

# Step 4: Preview Entry
Button: 👁️ Preview Entry
Result: ✅ Entry is valid! Review below and save if correct.

# Step 5: Review & Save
├─ See data table ✓
├─ See metrics ✓
├─ Check details ✓
└─ If satisfied:
    Button: 💾 Save Entry
    Result: ✅ Successfully saved! 🎉
```

---

## ✨ What Changed

### Before (❌ Auto-Save)
- Click "Submit & Save" → Data immediately saved to CSV
- No preview capability
- No way to review before committing

### After (✅ Preview-Before-Save)
- Click "👁️ Preview Entry" → Validates only (no save yet)
- Preview section appears with all data
- Review your entry in detail
- THEN decide: Save or Edit

---

## 🎯 3 Buttons, 3 Actions

### Button 1: 👁️ Preview Entry
```
Location: Inside the form
Action:   Validates all fields
Result:   If VALID  → Show preview section
          If INVALID → Show error messages (fix & retry)
Saves:    NO - Just validates
```

### Button 2: 💾 Save Entry
```
Location: In the preview section (appears after preview)
Action:   Writes entry to manual_user_entries.csv
Result:   ✅ Success message
          🎉 Balloons animation!
          📊 Stats updated
Saves:    YES - Entry persisted to CSV
```

### Button 3: ❌ Cancel & Edit
```
Location: In the preview section (appears after preview)
Action:   Closes preview, returns to form
Result:   Form values remain (not lost!)
          Can edit and preview again
Saves:    NO - Just closes preview
```

---

## 💡 Use Cases

### Use Case 1: Submit Data (Happy Path)
```
1. Login
2. Fill form ✓
3. Click "Preview Entry"
4. Review looks good
5. Click "Save Entry"
6. Done! Data saved
```

### Use Case 2: Catch a Mistake
```
1. Login
2. Fill form with wrong value ❌
3. Click "Preview Entry"
4. See preview and notice error
5. Click "Cancel & Edit"
6. Fix the field ✓
7. Click "Preview Entry" again
8. Looks good now
9. Click "Save Entry"
10. Done!
```

### Use Case 3: Change Your Mind
```
1. Login
2. Fill form
3. Click "Preview Entry"
4. Review says "Hmm, maybe later"
5. Click "Cancel & Edit"
6. Form still has data (not lost!)
7. Can save later or log out
```

---

## 🔍 What You'll See

### After Login - Input Form
```
┌─────────────────────────────────────┐
│ Employee Name:        [__________]  │
│ Total Emails:         [35_______]   │
│ Off-Hour Ratio:       [0.0857___]   │
│ Attachment Ratio:     [0.2571___]   │
│ Avg Email Size:       [30407____]   │
│ Avg Recipients:       [2.97_____]   │
│ ISO Z-Score:         [-0.161____]   │
│ LOF Z-Score:         [-0.346____]   │
│ Autoencoder Z-Score: [-0.561____]   │
│ Ensemble Score:      [-0.355____]   │
│ Risk Level:          [NORMAL▼]      │
│ Alert Flag:          [0▼]           │
│                                     │
│ 👁️ Preview Entry [button]            │
└─────────────────────────────────────┘
```

### After "Preview Entry" Success - Preview Section
```
┌─────────────────────────────────────┐
│ 👁️ Preview Your Entry               │
│ Review your data before saving       │
│ ┌─────────────────────────────────┐ │
│ │ user      | ACV0812             │ │
│ │ employee  | Alden Caesar        │ │
│ │ emails    | 35                  │ │
│ │ off_hour  | 0.0857              │ │
│ │ ... (all fields)                │ │
│ └─────────────────────────────────┘ │
│                                     │
│ User ID: ACV0812                    │
│ Employee: Alden Caesar              │
│ Risk Level: NORMAL                  │
│ Ensemble Score: -0.355              │
│                                     │
│ 📋 Detailed Field Breakdown  [▼]    │
│                                     │
│ ────────────────────────────────── │
│ 💾 Save Entry  |  ❌ Cancel & Edit  │
└─────────────────────────────────────┘
```

### After "Save Entry" Success
```
┌─────────────────────────────────────┐
│ ✅ Entry saved for user 'ACV0812'   │
│    Data is now eligible for         │
│    ensemble analysis.               │
│                                     │
│ 🎉 [Balloons animation]             │
│                                     │
│ ✅ Successfully Saved:              │
│ ┌─────────────────────────────────┐ │
│ │ user      | ACV0812             │ │
│ │ employee  | Alden Caesar        │ │
│ │ emails    | 35                  │ │
│ │ timestamp | 2026-01-23T...      │ │
│ └─────────────────────────────────┘ │
│                                     │
│ 📊 Total manual entries: 1          │
└─────────────────────────────────────┘
```

---

## ⚠️ Important Notes

### ✅ What Happens
- Passwords hashed with SHA-512 ✓
- Preview section validates fields ✓
- Data only saved on "💾 Save Entry" click ✓
- Timestamps auto-generated ✓
- Multiple users supported ✓
- Can edit and re-preview ✓

### ❌ What Does NOT Happen
- Passwords NOT stored plaintext ✓
- Data NOT saved until explicit save button ✓
- Duplicate entries NOT overwritten ✓
- Preview does NOT save (session only) ✓

---

## 🧪 Try It Now!

### Test 1: Quick Register & Submit
```
1. Register: username="demo", password="test123"
2. Login
3. Fill form with default values
4. Click "Preview Entry"
5. Click "Save Entry"
6. Done!
```

### Test 2: Validation Error
```
1. Login
2. Set "Off-Hour Ratio" to 5 (invalid)
3. Click "Preview Entry"
4. See error: "must be between 0 and 1"
5. Fix to 0.5
6. Click "Preview Entry"
7. Now success!
```

### Test 3: Cancel & Edit
```
1. Login
2. Fill form
3. Click "Preview Entry" → Success
4. Click "Cancel & Edit"
5. Preview disappears
6. Form still has data!
7. Change one value
8. Click "Preview Entry" again
9. See new value
10. Save new version
```

---

## 📊 Data Integration

After you save an entry, it:

✅ Appears in **Main Dashboard** (risk metrics)
✅ Used in **Model Evaluation** (ensemble scoring)
✅ Included in **Network Analysis** (network risk)
✅ Available for **Analytics** (trends, graphs)
✅ Eligible for **Comparative Analysis** (reports)

---

## 📞 Quick Help

| Problem | Solution |
|---------|----------|
| "Can't see form after login" | Try refresh (F5), check browser console (F12) |
| "Preview not working" | Ensure all fields filled with valid values |
| "Data not saved" | Click "💾 Save Entry" (not just Preview) |
| "Forgot password" | Contact administrator (no recovery in demo) |
| "Username taken" | Use different username for registration |

---

## 🎯 Key Takeaway

```
OLD: Fill form → Auto-save (no control)
NEW: Fill form → Preview → Decide → Save (you're in control!)
```

**You now have complete control over when your data is persisted!**

---

**Ready?** 
1. Go to "Secure User Input" tab
2. Register or Login
3. Fill form
4. Click "👁️ Preview Entry"
5. Click "💾 Save Entry"
6. Done! 🎉

**Questions?** See [SECURE_INPUT_GUIDE.md](SECURE_INPUT_GUIDE.md)
