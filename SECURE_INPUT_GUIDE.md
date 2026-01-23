# 🔐 Secure User Input Tab - Complete Guide

## Overview

The **"Secure User Input"** tab provides a two-step process for entering and submitting behavioral data:

1. **Authentication** - Register or login with username/password
2. **Data Entry & Preview** - Fill in behavioral metrics, preview, then save

---

## 🔑 Step 1: Authentication

### First-Time Users: Register

1. Go to the **"Secure User Input"** tab
2. Select **"Register New User"**
3. Enter:
   - **Username**: e.g., `ACV0812`, `test_user_001`
   - **Password**: Any secure password (will be SHA-512 hashed)
   - **Confirm Password**: Re-enter the password
4. Click **"✅ Register Account"**
5. See success message: "✅ User 'X' registered successfully!"
6. Refresh or click login to proceed

### Existing Users: Login

1. Go to the **"Secure User Input"** tab
2. Select **"Login Existing User"**
3. Enter:
   - **Username**: Your registered username
   - **Password**: Your registered password
4. Click **"🔓 Login"**
5. See success message: "✅ Welcome back, X!"
6. Dashboard automatically redirects to data entry form

---

## 📝 Step 2: Data Entry

After successful authentication, you'll see an **input form** with the following sections:

### Section A: Employee Information

```
Employee Name: [text input]
└─ Your full name or identifier
```

### Section B: Behavioral Metrics

```
Total Emails: [number input, default: 35]
└─ Total number of emails sent during monitoring period

Off-Hour Ratio: [float 0-1, default: 0.0857]
└─ Proportion of emails sent outside business hours (0.0 = 0%, 1.0 = 100%)

Attachment Ratio: [float 0-1, default: 0.2571]
└─ Proportion of emails with attachments

Average Email Size: [float, default: 30407.23]
└─ Average size of emails in bytes

Average Recipients: [float, default: 2.97]
└─ Average number of recipients per email
```

### Section C: Anomaly Scores (Z-Scores)

```
Isolation Forest Z-Score: [float, default: -0.161]
└─ Z-score from Isolation Forest anomaly detector

LOF Z-Score: [float, default: -0.346]
└─ Z-score from Local Outlier Factor detector

Autoencoder Z-Score: [float, default: -0.561]
└─ Z-score from Autoencoder reconstruction error

Ensemble Weighted Score: [float, default: -0.355]
└─ Weighted ensemble score (40% LOF + 30% IF + 30% AE)
```

### Section D: Assessment & Flags

```
Risk Level: [dropdown]
├─ NORMAL (default)
├─ LOW
├─ MEDIUM
├─ HIGH
└─ CRITICAL

Ensemble Alert Flag: [dropdown]
├─ 0 (No alert)
└─ 1 (Alert triggered)
```

---

## 👁️ Step 3: Preview & Save

### Workflow

```
┌─────────────────────────────────────────┐
│  Fill in all fields in the form         │
│  Review the "Status" indicator          │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Click "👁️ Preview Entry"               │
│  (Validates all fields)                 │
└──────────────┬──────────────────────────┘
               │
               ▼
        ┌─────────────┐
        │  Validation │
        └─────┬───────┘
              │
      ┌───────┴───────┐
      │               │
   VALID        INVALID
      │               │
      ▼               ▼
   PREVIEW    ERROR MESSAGES
      │        (Fix & Retry)
      │               
      ▼               
┌─────────────────────────────────────────┐
│  "Preview Your Entry" Section Shows     │
│  - Data table with all entered values   │
│  - Summary metrics (ID, Name, Risk...)  │
│  - Detailed breakdown (expandable)      │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
   💾 SAVE    ❌ CANCEL & EDIT
        │             │
        ▼             ▼
   SAVED       FORM STAYS
   TO CSV      (Make changes)
```

### Preview Section Features

After clicking **"👁️ Preview Entry"** (with no validation errors), you'll see:

1. **Data Table** - All your entered values in a formatted table
2. **Summary Metrics** - Quick view of:
   - User ID
   - Employee Name
   - Risk Level
   - Ensemble Score
3. **Detailed Breakdown** - Expandable section showing:
   - All behavioral metrics
   - All anomaly scores
   - Alert flags

### Saving Options

From the Preview section:

- **💾 Save Entry** - Saves data to `manual_user_entries.csv` with timestamp
- **❌ Cancel & Edit** - Returns to form to make changes (preview disappears)

---

## ✅ Validation Rules

The system validates your entry before showing preview. Errors will appear as:

```
❌ **Validation Errors - Please Fix:**
  • Error message 1
  • Error message 2
  • Error message 3
```

### Common Validation Rules

| Field | Rule | Example Error |
|-------|------|---------------|
| Employee Name | Cannot be empty | "Employee name cannot be empty." |
| Total Emails | Must be ≥ 0 | "Total emails must be ≥ 0." |
| Off-Hour Ratio | Must be 0-1 | "off_hour_ratio: must be between 0 and 1." |
| Attachment Ratio | Must be 0-1 | "attachment_ratio: must be between 0 and 1." |
| Avg Email Size | Must be ≥ 0 | "Average email size must be ≥ 0." |
| Avg Recipients | Must be ≥ 0 | "Average recipients must be ≥ 0." |
| Z-Scores | Typically -10 to +10 | "iso_z: z-score should typically be between -10 and +10." |
| Risk Level | Must be valid enum | "Risk level must be one of ['NORMAL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']." |
| Ensemble Alert | Must be 0 or 1 | "Ensemble alert must be 0 or 1." |

---

## 🔐 Security Features

### Password Hashing

✓ **SHA-512 Cryptographic Hashing**
- 128-character hexadecimal output
- Non-reversible (one-way function)
- Identical input always produces identical hash

✓ **Never Stored in Plaintext**
- Only the hash is saved to `users_auth.json`
- Plaintext password never logged
- Passwords not visible in UI (masked input)

✓ **Hash-Only Authentication**
- Login computes hash of provided password
- Compares hash against stored hash
- Grants access only if hashes match

### Session Security

✓ **Session State Management**
- Authentication persists until:
  - Browser tab closes
  - Sidebar "🔓 Logout" button clicked
  - Server restarts

✓ **Graceful Error Messages**
- No stack traces revealed
- No password hints
- No user enumeration attacks

---

## 📊 Data Persistence

### Where Is Data Saved?

After clicking **💾 Save Entry**, your data is saved to:

```
manual_user_entries.csv
```

Located in the project root directory alongside `app.py`.

### CSV Structure

```
timestamp                        | user      | employee_name | total_emails | ... | ensemble_weighted | risk_level | ensemble_alert
2026-01-23T15:30:45.123456+00:00 | ACV0812   | Alden Caesar  | 35           | ... | -0.355           | NORMAL     | 0
2026-01-23T15:35:20.987654+00:00 | test_user | John Doe      | 40           | ... | 0.250            | LOW        | 0
```

**Timestamp** is auto-generated in ISO 8601 format (UTC).

### Integration with Dashboard

Your submitted entries:

✅ Appear in **"Main Dashboard"** risk metrics
✅ Eligible for **"Model Evaluation"** ensemble scoring
✅ Included in **"Network Risk Analysis"** visualizations
✅ Available for **"Analytics & Graphs"** trend analysis
✅ Contribute to **"Comparative Analysis"** reports

---

## 🚀 Example Walkthrough

### Example: Register & Submit Entry

```
STEP 1: Register
─────────────────
1. Go to "Secure User Input" tab
2. Select "Register New User"
3. Username: "ACV0812"
4. Password: "SecurePass123!"
5. Confirm: "SecurePass123!"
6. Click "✅ Register Account"
7. Success! ✅ User 'ACV0812' registered successfully!

STEP 2: Login
─────────────
1. Select "Login Existing User"
2. Username: "ACV0812"
3. Password: "SecurePass123!"
4. Click "🔓 Login"
5. Success! ✅ Welcome back, ACV0812!
6. Redirected to data entry form

STEP 3: Fill Form
──────────────────
1. Employee Name: "Alden Caesar Velez"
2. Total Emails: 35
3. Off-Hour Ratio: 0.0857
4. Attachment Ratio: 0.2571
5. Avg Email Size: 30407.23
6. Avg Recipients: 2.97
7. Isolation Forest Z: -0.161
8. LOF Z: -0.346
9. Autoencoder Z: -0.561
10. Ensemble Score: -0.355
11. Risk Level: "NORMAL"
12. Alert Flag: 0

STEP 4: Preview
────────────────
1. Click "👁️ Preview Entry"
2. ✅ Entry is valid! Review below and save if correct.
3. See preview table with all values
4. Expand "📋 Detailed Field Breakdown"
5. Review metrics and scores

STEP 5: Save
─────────────
1. Click "💾 Save Entry"
2. ✅ Entry saved for user 'ACV0812'. Data is now eligible for ensemble analysis.
3. 🎉 Balloons animation!
4. See "✅ Successfully Saved:" with data table
5. "📊 Total manual entries saved: 1"
6. Data persisted to manual_user_entries.csv

COMPLETE!
```

---

## 📋 Submitted Data Status Section

After submission, you'll see a **"Submitted Data Status"** section showing:

```
┌─────────────────────────────────────────────────────────┐
│  Total Manual Entries: 5                                │
│  Your Entries (ACV0812): 2                              │
│  Baseline Users: 200                                    │
└─────────────────────────────────────────────────────────┘
```

And a **"Recent Submissions"** table displaying the 10 most recent entries (if any exist).

---

## ⚠️ Important Notes

### What DOES Happen

✅ Passwords are SHA-512 hashed
✅ Hash stored in `users_auth.json`
✅ Data saved to `manual_user_entries.csv`
✅ Timestamps auto-generated
✅ Data integrated into dashboard

### What DOES NOT Happen

❌ Passwords are NOT stored in plaintext
❌ Passwords are NOT logged
❌ Passwords are NOT transmitted over network (localhost only)
❌ Data is NOT saved until you click "💾 Save Entry"
❌ Duplicate entries are NOT auto-overwritten

### Password Recovery

⚠️ **NOT supported in demo mode**

If you forget your password:
- Contact your administrator
- Usernames can be checked in `users_auth.json`

---

## 🧪 Testing Scenarios

### Scenario 1: New User Workflow

```
1. Register: username="test_new", password="pass123"
2. Login with those credentials
3. Fill form with sample data
4. Click "Preview"
5. Verify preview shows correct values
6. Click "Save Entry"
7. Check manual_user_entries.csv for new row
```

### Scenario 2: Validation Error Handling

```
1. Login successfully
2. Clear "Off-Hour Ratio" field (leave empty or invalid)
3. Click "Preview Entry"
4. See error: "off_hour_ratio: must be a valid number."
5. Fix the field
6. Click "Preview Entry" again
7. Should now succeed
```

### Scenario 3: Cancel & Edit

```
1. Login
2. Fill form
3. Click "Preview Entry" → Success
4. Review preview
5. Click "❌ Cancel & Edit"
6. Preview disappears
7. Modify form fields
8. Click "Preview Entry" again with new values
9. Save new version
```

### Scenario 4: Check Data Persistence

```
1. Submit entry as user1
2. Logout
3. Login as user2
4. Submit entry as user2
5. Open manual_user_entries.csv
6. Verify both entries exist (not overwritten)
```

---

## 📞 Troubleshooting

### Issue: "Login Failed - User Not Found"

**Solution**: 
- Verify username is spelled correctly (case-sensitive)
- Register new user if this is first time
- Check `users_auth.json` to see registered usernames

### Issue: "Incorrect Password"

**Solution**:
- Verify you typed password correctly
- Remember passwords are case-sensitive
- Passwords should NOT have leading/trailing spaces

### Issue: Form Fields Not Showing After Login

**Solution**:
- Try refreshing the page (F5 or Ctrl+R)
- Check browser console for errors (F12)
- Ensure you logged in successfully (see "Welcome" message)
- Verify JavaScript is enabled

### Issue: "Preview Entry" Button Not Working

**Solution**:
- Ensure all fields are filled
- Check for validation errors in preview
- Try filling with example values provided
- Look for error messages in red text

### Issue: Data Not Saving

**Solution**:
- Verify you clicked "💾 Save Entry" (not just Preview)
- Check for success message (green checkmark)
- Verify `manual_user_entries.csv` exists in project directory
- Check file permissions (should be writable)

---

## 📚 Additional Resources

- **Authentication Guide**: [AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md)
- **Implementation Notes**: [IMPLEMENTATION_NOTES_AUTH.md](IMPLEMENTATION_NOTES_AUTH.md)
- **Security Documentation**: [SECURE_INPUT_QUICKSTART.md](SECURE_INPUT_QUICKSTART.md)

---

**Last Updated**: January 23, 2026
**Version**: 1.0
**Status**: Production Ready ✅
