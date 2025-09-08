#!/usr/bin/env python3
"""
Simple integration test to verify OPA project filtering works end-to-end
"""

import requests
import json
import sys

def test_opa_to_label_studio_flow():
    """Test the complete flow from OPA to Label Studio project filtering"""
    print("=== Complete OPA Integration Flow Test ===")
    
    # Step 1: Test OPA directly
    print("\n1. Testing OPA Server Response...")
    opa_url = "http://localhost:8181"
    
    users_to_test = {
        "hellf0rg0d@proton.me": {"expected_projects": ["project_B"], "expected_ids": [30]},
        "testing@example.com": {"expected_projects": ["project_A", "project_B", "project_C"], "expected_ids": [41, 30, 25]}
    }
    
    opa_results = {}
    
    for user, expected in users_to_test.items():
        try:
            payload = {"input": {"user": user}}
            response = requests.post(
                f"{opa_url}/v1/data/organization/rbac/user_projects",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                projects = result.get('result', [])
                print(f"  ✓ {user}: OPA returned {projects}")
                opa_results[user] = projects
                
                # Verify expected projects
                if set(projects) == set(expected["expected_projects"]):
                    print(f"    ✅ Correct projects returned")
                else:
                    print(f"    ❌ Expected {expected['expected_projects']}, got {projects}")
            else:
                print(f"  ✗ {user}: OPA error {response.status_code}")
                opa_results[user] = []
                
        except Exception as e:
            print(f"  ✗ {user}: Exception {e}")
            opa_results[user] = []
    
    # Step 2: Test project name to ID conversion
    print("\n2. Testing Project Name to ID Conversion...")
    name_to_id_mapping = {
        "project_A": 41,
        "project_B": 30, 
        "project_C": 25,
    }
    
    conversion_results = {}
    
    for user, projects in opa_results.items():
        project_ids = []
        for name in projects:
            if isinstance(name, str) and name in name_to_id_mapping:
                project_ids.append(name_to_id_mapping[name])
            elif isinstance(name, (int, str)) and str(name).isdigit():
                project_ids.append(int(name))
        
        conversion_results[user] = project_ids
        expected_ids = users_to_test[user]["expected_ids"]
        
        print(f"  ✓ {user}: {projects} → {project_ids}")
        
        if set(project_ids) == set(expected_ids):
            print(f"    ✅ Correct ID conversion")
        else:
            print(f"    ❌ Expected IDs {expected_ids}, got {project_ids}")
    
    # Step 3: Test Label Studio API endpoints
    print("\n3. Testing Label Studio OPA API Endpoints...")
    label_studio_url = "http://localhost:8080"
    
    endpoints_to_test = [
        "/api/opa/user-projects/",
        "/api/opa/clear-cache/"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{label_studio_url}{endpoint}")
            
            if response.status_code == 401:
                print(f"  ✓ {endpoint}: Requires authentication (expected)")
            elif response.status_code == 404:
                print(f"  ✗ {endpoint}: Not found - URL routing issue")
            elif response.status_code == 200:
                print(f"  ✓ {endpoint}: Accessible")
            else:
                print(f"  ? {endpoint}: Unexpected status {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ {endpoint}: Exception {e}")
    
    # Step 4: Summary and specific checks
    print("\n4. Key Validation Checks...")
    
    # Check hellf0rg0d@proton.me specifically
    hellf0rg0d_ids = conversion_results.get("hellf0rg0d@proton.me", [])
    if 30 in hellf0rg0d_ids:
        print("  ✅ hellf0rg0d@proton.me CAN access project ID 30")
    else:
        print("  ❌ hellf0rg0d@proton.me CANNOT access project ID 30")
    
    # Check testing@example.com
    testing_ids = conversion_results.get("testing@example.com", [])
    expected_testing_ids = {41, 30, 25}
    if expected_testing_ids.issubset(set(testing_ids)):
        print("  ✅ testing@example.com CAN access all expected projects")
    else:
        missing = expected_testing_ids - set(testing_ids)
        print(f"  ❌ testing@example.com missing projects: {missing}")
    
    return conversion_results

def test_potential_issues():
    """Test for common integration issues"""
    print("\n=== Potential Issues Check ===")
    
    issues_found = []
    
    # Check 1: OPA server accessibility
    try:
        response = requests.get("http://localhost:8181/health", timeout=2)
        if response.status_code != 200:
            issues_found.append("OPA server health check failed")
        else:
            print("✓ OPA server is healthy")
    except:
        issues_found.append("Cannot reach OPA server")
    
    # Check 2: Label Studio accessibility
    try:
        response = requests.get("http://localhost:8080/api/", timeout=2)
        if response.status_code not in [200, 401]:
            issues_found.append("Label Studio server not responding properly")
        else:
            print("✓ Label Studio server is accessible")
    except:
        issues_found.append("Cannot reach Label Studio server")
    
    # Check 3: OPA policy syntax
    try:
        payload = {"input": {"user": "hellf0rg0d@proton.me"}}
        response = requests.post(
            "http://localhost:8181/v1/data/organization/rbac/user_projects",
            json=payload,
            timeout=2
        )
        if response.status_code == 200:
            print("✓ OPA policy is working")
        else:
            issues_found.append(f"OPA policy error: {response.status_code}")
    except Exception as e:
        issues_found.append(f"OPA policy test failed: {e}")
    
    if issues_found:
        print("\n❌ Issues Found:")
        for issue in issues_found:
            print(f"  - {issue}")
    else:
        print("\n✅ No issues detected")
    
    return len(issues_found) == 0

def main():
    """Run complete integration test"""
    print("Label Studio OPA Integration - Complete Flow Test")
    print("=" * 60)
    
    # Run main flow test
    conversion_results = test_opa_to_label_studio_flow()
    
    # Check for issues
    no_issues = test_potential_issues()
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY:")
    
    hellf0rg0d_can_access_30 = 30 in conversion_results.get("hellf0rg0d@proton.me", [])
    testing_can_access_all = {41, 30, 25}.issubset(set(conversion_results.get("testing@example.com", [])))
    
    if hellf0rg0d_can_access_30:
        print("✅ hellf0rg0d@proton.me should be able to see project ID 30")
    else:
        print("❌ hellf0rg0d@proton.me will NOT see project ID 30")
    
    if testing_can_access_all:
        print("✅ testing@example.com should be able to see all projects")
    else:
        print("❌ testing@example.com will NOT see all expected projects")
    
    if no_issues and hellf0rg0d_can_access_30:
        print("\n🎉 Integration is working correctly!")
    else:
        print("\n⚠️  Integration may have issues - check above for details")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
