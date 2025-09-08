#!/usr/bin/env python3
"""
Debug script to test OPA integration with specific users
"""

import requests
import json
import sys

# Configuration
OPA_URL = "http://localhost:8181"

def test_opa_user_access(user_email):
    """Test OPA access for a specific user"""
    print(f"\n=== Testing OPA access for: {user_email} ===")
    
    try:
        # Test the OPA policy endpoint
        payload = {"input": {"user": user_email}}
        response = requests.post(
            f"{OPA_URL}/v1/data/organization/rbac/user_projects",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            projects = result.get('result', [])
            print(f"✓ OPA Response: {projects}")
            print(f"✓ Project count: {len(projects)}")
            
            # Convert to Label Studio IDs
            name_to_id_mapping = {
                "project_A": 41,
                "project_B": 30, 
                "project_C": 25,
            }
            
            project_ids = []
            for name in projects:
                if isinstance(name, str) and name in name_to_id_mapping:
                    project_ids.append(name_to_id_mapping[name])
                elif isinstance(name, (int, str)) and str(name).isdigit():
                    project_ids.append(int(name))
            
            print(f"✓ Converted to IDs: {project_ids}")
            return project_ids
            
        else:
            print(f"✗ OPA Error: {response.status_code}")
            print(f"✗ Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"✗ Exception: {e}")
        return []

def test_opa_server_health():
    """Test if OPA server is running"""
    print("\n=== Testing OPA Server Health ===")
    
    try:
        response = requests.get(f"{OPA_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ OPA server is healthy")
            return True
        else:
            print(f"✗ OPA health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot reach OPA server: {e}")
        return False

def main():
    """Run debug tests"""
    print("OPA Debug Test Suite")
    print("=" * 50)
    
    # Test OPA server health first
    if not test_opa_server_health():
        print("\n❌ OPA server is not accessible. Please start OPA server first.")
        sys.exit(1)
    
    # Test both users
    test_users = [
        "hellf0rg0d@proton.me",
        "testing@example.com"
    ]
    
    results = {}
    for user in test_users:
        results[user] = test_opa_user_access(user)
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"hellf0rg0d@proton.me should see project ID 30: {30 in results.get('hellf0rg0d@proton.me', [])}")
    print(f"testing@example.com should see project IDs 41,30,25: {set([41,30,25]).issubset(set(results.get('testing@example.com', [])))}")
    
    # Expected vs Actual
    print(f"\nExpected for hellf0rg0d@proton.me: [30]")
    print(f"Actual for hellf0rg0d@proton.me: {results.get('hellf0rg0d@proton.me', [])}")
    
    print(f"\nExpected for testing@example.com: [41, 30, 25]")
    print(f"Actual for testing@example.com: {results.get('testing@example.com', [])}")

if __name__ == "__main__":
    main()
