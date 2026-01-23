#!/usr/bin/env python3
# ============================================================================
# AUTHENTICATION SYSTEM TEST SUITE
# ============================================================================
# Validates SHA-512 hashing, registration, login, and CSV persistence
# ============================================================================

import os
import sys
import json
import pandas as pd
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.auth_utils import (
    hash_password,
    register_user,
    authenticate_user,
    load_users,
    validate_user_entry,
    save_manual_entry,
    get_user_entries_count,
    USERS_AUTH_FILE,
    MANUAL_ENTRIES_FILE
)


def test_password_hashing():
    """Test SHA-512 password hashing."""
    print("\n" + "="*70)
    print("TEST 1: PASSWORD HASHING (SHA-512)")
    print("="*70)
    
    password = "SecurePassword123!"
    hash1 = hash_password(password)
    hash2 = hash_password(password)
    
    print(f"Password: {password}")
    print(f"Hash 1:  {hash1}")
    print(f"Hash 2:  {hash2}")
    print(f"Hashes Match: {hash1 == hash2}")
    print(f"Hash Length: {len(hash1)} characters (SHA-512 = 128 chars)")
    
    assert hash1 == hash2, "Identical passwords should produce identical hashes"
    assert len(hash1) == 128, "SHA-512 hash should be 128 characters"
    print("✅ PASS: Password hashing works correctly")


def test_user_registration():
    """Test user registration flow."""
    print("\n" + "="*70)
    print("TEST 2: USER REGISTRATION")
    print("="*70)
    
    # Clean up test file
    if os.path.exists(USERS_AUTH_FILE):
        os.remove(USERS_AUTH_FILE)
    
    # Test new user
    success, msg = register_user("test_user_001", "password123")
    print(f"Register new user: {msg}")
    assert success, "Should successfully register new user"
    
    # Verify stored in file
    users = load_users()
    assert "test_user_001" in users, "User should be in registry"
    assert "password_hash" in users["test_user_001"], "Should store hash"
    assert "created_at" in users["test_user_001"], "Should store timestamp"
    print(f"Stored user data: {json.dumps(users['test_user_001'], indent=2)}")
    
    # Test duplicate registration
    success, msg = register_user("test_user_001", "different_password")
    print(f"Attempt duplicate registration: {msg}")
    assert not success, "Should reject duplicate username"
    
    # Test empty fields
    success, msg = register_user("", "password")
    assert not success, "Should reject empty username"
    
    success, msg = register_user("user", "")
    assert not success, "Should reject empty password"
    
    print("✅ PASS: User registration works correctly")


def test_authentication():
    """Test login authentication."""
    print("\n" + "="*70)
    print("TEST 3: USER AUTHENTICATION (Login)")
    print("="*70)
    
    # Use registered user from previous test
    username = "test_user_001"
    correct_password = "password123"
    wrong_password = "incorrect_password"
    
    # Test correct password
    success, msg = authenticate_user(username, correct_password)
    print(f"Login with correct password: {msg}")
    assert success, "Should authenticate with correct password"
    
    # Test wrong password
    success, msg = authenticate_user(username, wrong_password)
    print(f"Login with wrong password: {msg}")
    assert not success, "Should reject incorrect password"
    
    # Test nonexistent user
    success, msg = authenticate_user("nonexistent_user", "any_password")
    print(f"Login with nonexistent user: {msg}")
    assert not success, "Should reject nonexistent user"
    
    print("✅ PASS: Authentication works correctly")


def test_data_validation():
    """Test user entry validation."""
    print("\n" + "="*70)
    print("TEST 4: DATA VALIDATION")
    print("="*70)
    
    # Valid entry
    valid_entry = {
        'user': 'test_user_001',
        'employee_name': 'John Doe',
        'total_emails': 35,
        'off_hour_ratio': 0.0857,
        'attachment_ratio': 0.2571,
        'avg_email_size': 30407.23,
        'avg_recipients': 2.97,
        'iso_z': -0.161,
        'lof_z': -0.346,
        'ae_z': -0.561,
        'ensemble_weighted': -0.355,
        'risk_level': 'NORMAL',
        'ensemble_alert': 0
    }
    
    is_valid, errors = validate_user_entry(valid_entry)
    print(f"Valid entry validation: {is_valid}")
    assert is_valid, f"Valid entry should pass: {errors}"
    
    # Invalid: ratio out of range
    invalid_entry = valid_entry.copy()
    invalid_entry['off_hour_ratio'] = 1.5
    is_valid, errors = validate_user_entry(invalid_entry)
    print(f"Invalid ratio (1.5): {is_valid}, Errors: {errors}")
    assert not is_valid, "Should reject ratio > 1"
    
    # Invalid: empty employee name
    invalid_entry = valid_entry.copy()
    invalid_entry['employee_name'] = ''
    is_valid, errors = validate_user_entry(invalid_entry)
    print(f"Empty employee name: {is_valid}, Errors: {errors}")
    assert not is_valid, "Should reject empty employee name"
    
    # Invalid: wrong risk level
    invalid_entry = valid_entry.copy()
    invalid_entry['risk_level'] = 'INVALID_LEVEL'
    is_valid, errors = validate_user_entry(invalid_entry)
    print(f"Invalid risk level: {is_valid}, Errors: {errors}")
    assert not is_valid, "Should reject invalid risk level"
    
    # Invalid: ensemble_alert not 0 or 1
    invalid_entry = valid_entry.copy()
    invalid_entry['ensemble_alert'] = 5
    is_valid, errors = validate_user_entry(invalid_entry)
    print(f"Invalid ensemble_alert (5): {is_valid}, Errors: {errors}")
    assert not is_valid, "Should reject ensemble_alert != 0 or 1"
    
    print("✅ PASS: Data validation works correctly")


def test_csv_persistence():
    """Test CSV persistence."""
    print("\n" + "="*70)
    print("TEST 5: CSV PERSISTENCE")
    print("="*70)
    
    # Clean up test file
    if os.path.exists(MANUAL_ENTRIES_FILE):
        os.remove(MANUAL_ENTRIES_FILE)
    
    # Create valid entry
    entry = {
        'user': 'test_user_001',
        'employee_name': 'John Doe',
        'total_emails': 35,
        'off_hour_ratio': 0.0857,
        'attachment_ratio': 0.2571,
        'avg_email_size': 30407.23,
        'avg_recipients': 2.97,
        'iso_z': -0.161,
        'lof_z': -0.346,
        'ae_z': -0.561,
        'ensemble_weighted': -0.355,
        'risk_level': 'NORMAL',
        'ensemble_alert': 0
    }
    
    # Save first entry
    success, msg = save_manual_entry(entry)
    print(f"Save entry 1: {msg}")
    assert success, "Should successfully save entry"
    
    # Verify file created
    assert os.path.exists(MANUAL_ENTRIES_FILE), "CSV file should be created"
    
    # Check count
    count1 = get_user_entries_count()
    print(f"Entry count after 1st save: {count1}")
    assert count1 == 1, "Should have 1 entry"
    
    # Save second entry
    entry2 = entry.copy()
    entry2['employee_name'] = 'Jane Smith'
    success, msg = save_manual_entry(entry2)
    print(f"Save entry 2: {msg}")
    assert success, "Should successfully save second entry"
    
    # Check count
    count2 = get_user_entries_count()
    print(f"Entry count after 2nd save: {count2}")
    assert count2 == 2, "Should have 2 entries"
    
    # Read and verify CSV
    df = pd.read_csv(MANUAL_ENTRIES_FILE)
    print(f"\nSaved CSV structure:")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {df.columns.tolist()}")
    print(f"  Has timestamp: {'timestamp' in df.columns}")
    
    assert len(df) == 2, "CSV should have 2 rows"
    assert 'timestamp' in df.columns, "Should have timestamp column"
    assert df['user'].unique().tolist() == ['test_user_001'], "Both rows should be from same user"
    
    print("\nFirst entry:")
    print(df.iloc[0])
    
    print("✅ PASS: CSV persistence works correctly")


def test_multiple_users():
    """Test multiple users in system."""
    print("\n" + "="*70)
    print("TEST 6: MULTIPLE USERS & ISOLATION")
    print("="*70)
    
    # Register second user
    success, msg = register_user("test_user_002", "password456")
    print(f"Register user 2: {msg}")
    assert success, "Should register second user"
    
    # Verify both users in registry
    users = load_users()
    assert "test_user_001" in users, "User 1 should exist"
    assert "test_user_002" in users, "User 2 should exist"
    print(f"Total users in registry: {len(users)}")
    
    # Authenticate user 2
    success, msg = authenticate_user("test_user_002", "password456")
    print(f"Authenticate user 2: {msg}")
    assert success, "Should authenticate user 2"
    
    # Save entry for user 2
    entry_user2 = {
        'user': 'test_user_002',
        'employee_name': 'Jane Smith',
        'total_emails': 40,
        'off_hour_ratio': 0.15,
        'attachment_ratio': 0.30,
        'avg_email_size': 25000.0,
        'avg_recipients': 3.5,
        'iso_z': 0.5,
        'lof_z': 0.3,
        'ae_z': 0.2,
        'ensemble_weighted': 0.35,
        'risk_level': 'LOW',
        'ensemble_alert': 0
    }
    
    success, msg = save_manual_entry(entry_user2)
    print(f"Save entry for user 2: {msg}")
    assert success, "Should save entry for user 2"
    
    # Verify CSV has entries from both users
    df = pd.read_csv(MANUAL_ENTRIES_FILE)
    print(f"\nTotal entries in CSV: {len(df)}")
    print(f"Unique users: {df['user'].unique().tolist()}")
    
    user1_count = len(df[df['user'] == 'test_user_001'])
    user2_count = len(df[df['user'] == 'test_user_002'])
    print(f"User 1 entries: {user1_count}")
    print(f"User 2 entries: {user2_count}")
    
    assert user1_count == 2, "User 1 should have 2 entries"
    assert user2_count == 1, "User 2 should have 1 entry"
    
    print("✅ PASS: Multiple users work correctly with proper isolation")


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "="*70)
    print("AUTHENTICATION SYSTEM TEST SUITE")
    print("="*70)
    
    tests = [
        test_password_hashing,
        test_user_registration,
        test_authentication,
        test_data_validation,
        test_csv_persistence,
        test_multiple_users,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"❌ FAIL: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ ERROR: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {passed + failed}")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️ {failed} test(s) failed")
    
    print("="*70)
    
    # File summary
    print("\n📁 Generated Files:")
    if os.path.exists(USERS_AUTH_FILE):
        print(f"  ✅ {USERS_AUTH_FILE} (user registry)")
        with open(USERS_AUTH_FILE, 'r') as f:
            data = json.load(f)
        print(f"     - Users: {list(data.keys())}")
    
    if os.path.exists(MANUAL_ENTRIES_FILE):
        df = pd.read_csv(MANUAL_ENTRIES_FILE)
        print(f"  ✅ {MANUAL_ENTRIES_FILE} ({len(df)} entries)")
        print(f"     - Columns: {df.shape[1]}")
        print(f"     - Users: {df['user'].unique().tolist()}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
