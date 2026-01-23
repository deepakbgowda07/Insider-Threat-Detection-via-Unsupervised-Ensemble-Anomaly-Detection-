# ============================================================================
# SECURE AUTHENTICATION UTILITIES — SHA-512 Password Hashing
# ============================================================================
# Provides user registration, login validation, and credential management.
# Passwords are NEVER stored or logged in plaintext.
# ============================================================================

import hashlib
import json
import os
from datetime import datetime, timezone
import pandas as pd

# ============================================================================
# FILE PATHS
# ============================================================================

USERS_AUTH_FILE = "users_auth.json"
MANUAL_ENTRIES_FILE = "manual_user_entries.csv"


# ============================================================================
# PASSWORD HASHING
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using SHA-512.
    
    Args:
        password (str): Plain text password
        
    Returns:
        str: SHA-512 hexadecimal hash (128 characters)
        
    Security Notes:
        - Uses hashlib.sha512() for cryptographic hashing
        - Output is 128-character hex string
        - Not salted (note: in production, use argon2 or bcrypt with salt)
        - Each call produces identical hash for same input
    """
    return hashlib.sha512(password.encode()).hexdigest()


# ============================================================================
# CREDENTIAL STORAGE & MANAGEMENT
# ============================================================================

def load_users() -> dict:
    """
    Load user credentials from users_auth.json.
    Creates empty file if doesn't exist.
    
    Returns:
        dict: Format {'username': {'password_hash': 'hex_string', 'created_at': 'ISO_TIMESTAMP'}}
    """
    if not os.path.exists(USERS_AUTH_FILE):
        return {}
    
    try:
        with open(USERS_AUTH_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_users(users: dict) -> None:
    """
    Save user credentials to users_auth.json.
    
    Args:
        users (dict): User registry to persist
        
    Raises:
        IOError: If file cannot be written
    """
    with open(USERS_AUTH_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def register_user(username: str, password: str) -> tuple[bool, str]:
    """
    Register a new user with hashed password.
    
    Args:
        username (str): Username (must be unique)
        password (str): Plain text password (will be hashed)
        
    Returns:
        tuple: (success: bool, message: str)
        
    Rules:
        - Username must not already exist
        - Password must not be empty
        - Creates record with timestamp
    """
    if not username or not username.strip():
        return False, "❌ Username cannot be empty."
    
    if not password or not password.strip():
        return False, "❌ Password cannot be empty."
    
    users = load_users()
    
    if username in users:
        return False, f"❌ User '{username}' already exists. Please log in or use a different username."
    
    # Store hashed password + metadata
    users[username] = {
        "password_hash": hash_password(password),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    save_users(users)
    return True, f"✅ User '{username}' registered successfully!"


def authenticate_user(username: str, password: str) -> tuple[bool, str]:
    """
    Validate user credentials against stored hash.
    
    Args:
        username (str): Username to authenticate
        password (str): Plain text password attempt
        
    Returns:
        tuple: (success: bool, message: str)
        
    Security:
        - Compares SHA-512 hashes only
        - No plaintext password comparison
        - Graceful error messages (no stack traces)
    """
    if not username or not password:
        return False, "❌ Username and password required."
    
    users = load_users()
    
    if username not in users:
        return False, f"❌ User '{username}' not found. Please register first."
    
    stored_hash = users[username]["password_hash"]
    provided_hash = hash_password(password)
    
    if stored_hash == provided_hash:
        return True, f"✅ Welcome back, {username}!"
    else:
        return False, "❌ Incorrect password. Please try again."


# ============================================================================
# DATA VALIDATION & PERSISTENCE
# ============================================================================

def validate_user_entry(entry: dict) -> tuple[bool, list]:
    """
    Validate structured user input before persistence.
    
    Args:
        entry (dict): User input dictionary with keys:
            - user, employee_name, total_emails, off_hour_ratio, attachment_ratio,
            - avg_email_size, avg_recipients, iso_z, lof_z, ae_z, 
            - ensemble_weighted, risk_level, ensemble_alert
            
    Returns:
        tuple: (is_valid: bool, errors: list[str])
    """
    errors = []
    
    # Required string fields
    if not entry.get('user', '').strip():
        errors.append("Username cannot be empty.")
    if not entry.get('employee_name', '').strip():
        errors.append("Employee name cannot be empty.")
    
    # Total emails (positive integer)
    try:
        total_emails = int(entry.get('total_emails', 0))
        if total_emails < 0:
            errors.append("Total emails must be ≥ 0.")
    except (ValueError, TypeError):
        errors.append("Total emails must be a valid integer.")
    
    # Ratios (0-1 range)
    ratio_fields = ['off_hour_ratio', 'attachment_ratio']
    for field in ratio_fields:
        try:
            value = float(entry.get(field, 0))
            if not (0 <= value <= 1):
                errors.append(f"{field}: must be between 0 and 1.")
        except (ValueError, TypeError):
            errors.append(f"{field}: must be a valid number.")
    
    # Average email size (non-negative float)
    try:
        avg_size = float(entry.get('avg_email_size', 0))
        if avg_size < 0:
            errors.append("Average email size must be ≥ 0.")
    except (ValueError, TypeError):
        errors.append("Average email size must be a valid number.")
    
    # Average recipients (non-negative float)
    try:
        avg_recip = float(entry.get('avg_recipients', 0))
        if avg_recip < 0:
            errors.append("Average recipients must be ≥ 0.")
    except (ValueError, TypeError):
        errors.append("Average recipients must be a valid number.")
    
    # Z-scores (numeric, typically -5 to +5)
    z_score_fields = ['iso_z', 'lof_z', 'ae_z', 'ensemble_weighted']
    for field in z_score_fields:
        try:
            value = float(entry.get(field, 0))
            if not (-10 <= value <= 10):
                errors.append(f"{field}: z-score should typically be between -10 and +10.")
        except (ValueError, TypeError):
            errors.append(f"{field}: must be a valid number.")
    
    # Risk level (categorical)
    valid_risk_levels = ["NORMAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    if entry.get('risk_level', '').upper() not in valid_risk_levels:
        errors.append(f"Risk level must be one of {valid_risk_levels}.")
    
    # Ensemble alert (0 or 1)
    try:
        alert = int(entry.get('ensemble_alert', 0))
        if alert not in [0, 1]:
            errors.append("Ensemble alert must be 0 or 1.")
    except (ValueError, TypeError):
        errors.append("Ensemble alert must be 0 or 1.")
    
    return len(errors) == 0, errors


def save_manual_entry(entry: dict) -> tuple[bool, str]:
    """
    Persist user entry to manual_user_entries.csv.
    Appends new row or creates file if doesn't exist.
    
    Args:
        entry (dict): Validated user entry
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Add automatic timestamp
        entry['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Create DataFrame with single row
        new_row = pd.DataFrame([entry])
        
        # Check if file exists and append or create
        if os.path.exists(MANUAL_ENTRIES_FILE):
            existing_df = pd.read_csv(MANUAL_ENTRIES_FILE)
            updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            updated_df.to_csv(MANUAL_ENTRIES_FILE, index=False)
        else:
            new_row.to_csv(MANUAL_ENTRIES_FILE, index=False)
        
        return True, f"✅ Entry saved for user '{entry['user']}'. Data is now eligible for ensemble analysis."
    
    except Exception as e:
        return False, f"❌ Error saving entry: {str(e)}"


def get_user_entries_count() -> int:
    """
    Get count of saved manual entries.
    
    Returns:
        int: Number of rows in manual_user_entries.csv
    """
    if not os.path.exists(MANUAL_ENTRIES_FILE):
        return 0
    try:
        df = pd.read_csv(MANUAL_ENTRIES_FILE)
        return len(df)
    except:
        return 0


# ============================================================================
# SESSION STATE MANAGEMENT (for Streamlit)
# ============================================================================

def init_auth_session():
    """
    Initialize authentication session state in Streamlit.
    Call this at app startup.
    """
    import streamlit as st
    
    if 'auth_logged_in' not in st.session_state:
        st.session_state.auth_logged_in = False
    if 'auth_username' not in st.session_state:
        st.session_state.auth_username = None
    if 'auth_employee_name' not in st.session_state:
        st.session_state.auth_employee_name = None


def is_authenticated() -> bool:
    """Check if user is authenticated in current session."""
    import streamlit as st
    return st.session_state.get('auth_logged_in', False)


def get_current_user() -> str:
    """Get authenticated username or None."""
    import streamlit as st
    return st.session_state.get('auth_username', None)


def logout():
    """Clear authentication session."""
    import streamlit as st
    st.session_state.auth_logged_in = False
    st.session_state.auth_username = None
    st.session_state.auth_employee_name = None
