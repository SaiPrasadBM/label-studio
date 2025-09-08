#!/usr/bin/env python3
"""
Test script to trigger OPA integration and see debug logs
"""

import requests
import json
import time

def trigger_opa_integration():
    """Try to trigger OPA integration calls to see debug logs"""
    print("=== Triggering OPA Integration to See Debug Logs ===")
    
    # Test the OPA user projects endpoint with authentication
    try:
        # First, try to access the endpoint without auth to see behavior
        response = requests.get("http://localhost:8080/api/opa/user-projects/")
        
        if response.status_code == 401:
            print("✓ OPA endpoint requires authentication")
            print("  This means the endpoint exists and is properly configured")
        elif response.status_code == 404:
            print("❌ OPA endpoint not found - URL routing issue")
        else:
            print(f"? Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error accessing OPA endpoint: {e}")
    
    # Try to access projects API to see if it triggers filtering
    try:
        response = requests.get("http://localhost:8080/api/projects/")
        
        if response.status_code == 401:
            print("✓ Projects API requires authentication")
            print("  When hellf0rg0d@proton.me logs in, this should trigger OPA filtering")
        else:
            print(f"? Projects API response: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error accessing projects API: {e}")

def check_debug_logs_instructions():
    """Provide instructions for checking debug logs"""
    print("\n=== Debug Logging Instructions ===")
    
    print("1. I've added debug logging to opa_integration.py")
    print("   - All OPA calls will now print debug messages")
    print("   - You'll see when OPA integration is triggered")
    
    print("\n2. To see the debug logs:")
    print("   - Start/restart Label Studio server")
    print("   - Log in as hellf0rg0d@proton.me")
    print("   - Check the server console/logs for [OPA DEBUG] messages")
    
    print("\n3. Expected debug output when user logs in:")
    print("   [OPA DEBUG] get_user_accessible_projects called for user: hellf0rg0d@proton.me")
    print("   [OPA DEBUG] Getting projects for user: hellf0rg0d@proton.me")
    print("   [OPA DEBUG] Making OPA request to http://localhost:8181")
    print("   [OPA DEBUG] OPA returned projects: ['project_B']")
    print("   [OPA DEBUG] Converted to project IDs: [30]")
    print("   [OPA DEBUG] Final accessible projects for hellf0rg0d@proton.me: [30]")
    
    print("\n4. If you don't see these messages:")
    print("   - OPA integration is not being called")
    print("   - Check if the integration is properly imported/configured")
    print("   - Verify ProjectManager.for_user() is being used in views")

def test_project_30_existence():
    """Check if project 30 actually exists"""
    print("\n=== Testing Project 30 Existence ===")
    
    # Direct OPA test
    try:
        payload = {"input": {"user": "hellf0rg0d@proton.me"}}
        response = requests.post(
            "http://localhost:8181/v1/data/organization/rbac/user_projects",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            projects = result.get('result', [])
            print(f"✓ OPA says hellf0rg0d@proton.me can access: {projects}")
            
            if 'project_B' in projects:
                print("✓ project_B is in the list (should map to ID 30)")
            else:
                print("❌ project_B is NOT in the list")
        else:
            print(f"✗ OPA error: {response.status_code}")
            
    except Exception as e:
        print(f"✗ OPA test failed: {e}")
    
    print("\n📋 Next Steps:")
    print("1. Check if project ID 30 exists in Label Studio database")
    print("2. Log in as admin/superuser and verify project 30 is visible")
    print("3. If project 30 doesn't exist, create it or update the mapping")
    print("4. Check Label Studio server logs for [OPA DEBUG] messages when hellf0rg0d@proton.me logs in")

def main():
    """Run debug tests"""
    print("OPA Integration Debug Test")
    print("=" * 40)
    
    trigger_opa_integration()
    check_debug_logs_instructions()
    test_project_30_existence()
    
    print("\n" + "=" * 40)
    print("🔍 SUMMARY:")
    print("- Debug logging is now active in OPA integration")
    print("- Log in as hellf0rg0d@proton.me to see debug output")
    print("- Check if project ID 30 exists in the database")
    print("- Verify OPA integration is being called by Label Studio")

if __name__ == "__main__":
    main()
