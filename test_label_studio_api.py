#!/usr/bin/env python3
"""
Test script to verify Label Studio API integration with OPA for specific users
"""

import requests
import json
import sys
import os

# Configuration
LABEL_STUDIO_URL = "http://localhost:8080"
OPA_URL = "http://localhost:8181"

def test_opa_endpoint_direct(user_email):
    """Test OPA endpoint directly"""
    print(f"\n=== Direct OPA Test for {user_email} ===")
    
    try:
        payload = {"input": {"user": user_email}}
        response = requests.post(
            f"{OPA_URL}/v1/data/organization/rbac/user_projects",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            projects = result.get('result', [])
            print(f"✓ OPA Direct Response: {projects}")
            return projects
        else:
            print(f"✗ OPA Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"✗ OPA Exception: {e}")
        return []

def test_label_studio_opa_api(user_email, password="password123"):
    """Test Label Studio's OPA integration API endpoints"""
    print(f"\n=== Label Studio OPA API Test for {user_email} ===")
    
    session = requests.Session()
    
    try:
        # Try to get CSRF token first
        csrf_response = session.get(f"{LABEL_STUDIO_URL}/api/")
        if csrf_response.status_code == 200:
            print("✓ Connected to Label Studio")
        else:
            print(f"⚠ Label Studio connection: {csrf_response.status_code}")
        
        # Test the OPA user projects endpoint (without auth first to see behavior)
        opa_response = session.get(f"{LABEL_STUDIO_URL}/api/opa/user-projects/")
        
        if opa_response.status_code == 401:
            print("✓ OPA endpoint requires authentication (expected)")
        elif opa_response.status_code == 404:
            print("✗ OPA endpoint not found - URL routing issue")
        elif opa_response.status_code == 200:
            data = opa_response.json()
            print(f"✓ OPA endpoint accessible: {data}")
        else:
            print(f"? Unexpected response: {opa_response.status_code} - {opa_response.text}")
            
        return opa_response.status_code
        
    except Exception as e:
        print(f"✗ Label Studio API Exception: {e}")
        return None

def test_project_visibility_simulation():
    """Simulate project filtering logic"""
    print(f"\n=== Project Filtering Simulation ===")
    
    # Simulate the OPA integration logic
    users_to_test = [
        "hellf0rg0d@proton.me",
        "testing@example.com"
    ]
    
    name_to_id_mapping = {
        "project_A": 41,
        "project_B": 30, 
        "project_C": 25,
    }
    
    for user in users_to_test:
        print(f"\n--- Testing {user} ---")
        
        # Get OPA response
        opa_projects = test_opa_endpoint_direct(user)
        
        # Convert to IDs (simulate the integration logic)
        project_ids = []
        for name in opa_projects:
            if isinstance(name, str) and name in name_to_id_mapping:
                project_ids.append(name_to_id_mapping[name])
            elif isinstance(name, (int, str)) and str(name).isdigit():
                project_ids.append(int(name))
        
        print(f"✓ User {user} should see project IDs: {project_ids}")
        
        # Check specific expectations
        if user == "hellf0rg0d@proton.me":
            if 30 in project_ids:
                print("✅ hellf0rg0d@proton.me can access project ID 30 ✓")
            else:
                print("❌ hellf0rg0d@proton.me CANNOT access project ID 30 ✗")
        
        if user == "testing@example.com":
            expected = {41, 30, 25}
            actual = set(project_ids)
            if expected.issubset(actual):
                print("✅ testing@example.com can access all expected projects ✓")
            else:
                missing = expected - actual
                print(f"❌ testing@example.com missing projects: {missing} ✗")

def test_opa_cache_clearing():
    """Test OPA cache clearing functionality"""
    print(f"\n=== OPA Cache Test ===")
    
    try:
        # Test cache clearing endpoint
        response = requests.post(f"{LABEL_STUDIO_URL}/api/opa/clear-cache/")
        
        if response.status_code == 401:
            print("✓ Cache clearing endpoint requires authentication (expected)")
        elif response.status_code == 404:
            print("✗ Cache clearing endpoint not found")
        elif response.status_code == 200:
            print("✓ Cache clearing endpoint accessible")
        else:
            print(f"? Cache clearing response: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Cache test exception: {e}")

def main():
    """Run all API tests"""
    print("Label Studio OPA Integration API Tests")
    print("=" * 60)
    
    # Test users
    test_users = [
        "hellf0rg0d@proton.me",
        "testing@example.com"
    ]
    
    # Test 1: Direct OPA access
    print("\n🔍 Testing Direct OPA Access...")
    for user in test_users:
        test_opa_endpoint_direct(user)
    
    # Test 2: Label Studio OPA API endpoints
    print("\n🔍 Testing Label Studio OPA API Endpoints...")
    for user in test_users:
        test_label_studio_opa_api(user)
    
    # Test 3: Project filtering simulation
    print("\n🔍 Testing Project Filtering Logic...")
    test_project_visibility_simulation()
    
    # Test 4: Cache clearing
    print("\n🔍 Testing Cache Functionality...")
    test_opa_cache_clearing()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 KEY FINDINGS:")
    print("- Check if hellf0rg0d@proton.me gets project ID 30")
    print("- Check if Label Studio OPA endpoints are accessible")
    print("- Verify project filtering logic works correctly")
    print("=" * 60)

if __name__ == "__main__":
    main()
