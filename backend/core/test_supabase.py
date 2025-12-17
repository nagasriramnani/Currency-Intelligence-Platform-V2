"""
Test script to verify Supabase connection and table setup.
Run this after creating tables in Supabase SQL Editor.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from core.database import (
    is_supabase_configured,
    check_database_health,
    save_fx_rate,
    get_latest_rates,
    save_alert,
    get_unacknowledged_alerts
)
from datetime import date


def test_supabase_connection():
    """Test basic Supabase connectivity."""
    print("=" * 60)
    print("Supabase Connection Test")
    print("=" * 60)
    
    # Check configuration
    print("\n1. Checking configuration...")
    if is_supabase_configured():
        print("   [OK] Supabase client initialized")
    else:
        print("   [FAIL] Supabase not configured. Check SUPABASE_URL and SUPABASE_KEY in .env")
        return False
    
    # Health check
    print("\n2. Testing database health...")
    health = check_database_health()
    print(f"   Status: {health['status']}")
    print(f"   Message: {health['message']}")
    
    if health['status'] != 'connected':
        print("   [FAIL] Could not connect to database")
        print("   Make sure you've run the SQL schema in Supabase dashboard")
        return False
    
    print("   [OK] Database connection healthy")
    
    # Test insert
    print("\n3. Testing FX rate insert...")
    success = save_fx_rate(
        currency_pair="EUR",
        rate=0.8520,
        record_date=date.today(),
        source="test"
    )
    if success:
        print("   [OK] Test rate inserted successfully")
    else:
        print("   [FAIL] Could not insert test rate")
        print("   Make sure the fx_rates table exists")
        return False
    
    # Test query
    print("\n4. Testing FX rate query...")
    latest = get_latest_rates()
    if "EUR" in latest:
        print(f"   [OK] Retrieved EUR rate: {latest['EUR']['rate']}")
    else:
        print("   [WARN] No EUR rate found (this is OK if table is empty)")
    
    # Test alert insert
    print("\n5. Testing alert insert...")
    success = save_alert(
        title="Test Alert",
        message="Supabase integration test successful",
        severity="info"
    )
    if success:
        print("   [OK] Test alert inserted successfully")
    else:
        print("   [FAIL] Could not insert test alert")
        return False
    
    # Test alert query
    print("\n6. Testing alert query...")
    alerts = get_unacknowledged_alerts(limit=5)
    print(f"   [OK] Retrieved {len(alerts)} unacknowledged alerts")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED - Supabase integration is working!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_supabase_connection()
    sys.exit(0 if success else 1)
