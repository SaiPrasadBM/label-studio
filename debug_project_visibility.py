#!/usr/bin/env python3
"""
Debug script to check why project ID 30 is not visible in Label Studio UI
"""

import requests
import json
import sys

def test_project_existence():
    """Check if project ID 30 actually exists in the database"""
    print("=== Checking Project Existence ===")
    
    # Test via Label Studio API (requires auth, but we can see the response)
    try:
        response = requests.get("http://localhost:8080/api/projects/")
        
        if response.status_code == 401:
            print("✓ Projects API requires authentication (expected)")
            print("  Need to test with authenticated user to see actual projects")
        elif response.status_code == 200:
            projects = response.json()
            print(f"✓ Found {len(projects)} projects")
            
            project_30_exists = any(p.get('id') == 30 for p in projects)
            if project_30_exists:
                print("✅ Project ID 30 exists in database")
            else:
                print("❌ Project ID 30 does NOT exist in database")
                
        else:
            print(f"? Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error checking projects: {e}")

def test_opa_integration_in_label_studio():
    """Test if OPA integration is being called by Label Studio"""
    print("\n=== Testing OPA Integration in Label Studio ===")
    
    # Check if the OPA integration endpoints are working
    endpoints = [
        "/api/opa/user-projects/",
        "/api/opa/clear-cache/"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8080{endpoint}")
            
            if response.status_code == 401:
                print(f"✓ {endpoint} requires authentication")
            elif response.status_code == 404:
                print(f"❌ {endpoint} not found - integration not properly configured")
            else:
                print(f"? {endpoint} returned {response.status_code}")
                
        except Exception as e:
            print(f"✗ {endpoint} error: {e}")

def test_user_authentication():
    """Test user authentication and session"""
    print("\n=== Testing User Authentication ===")
    
    # Try to access a protected endpoint to see auth behavior
    try:
        session = requests.Session()
        
        # Try to get user info
        response = session.get("http://localhost:8080/api/current-user/")
        
        if response.status_code == 401:
            print("✓ User authentication required (expected)")
            print("  User hellf0rg0d@proton.me needs to be logged in to see filtered projects")
        elif response.status_code == 200:
            user_data = response.json()
            print(f"✓ User authenticated: {user_data.get('email', 'unknown')}")
        else:
            print(f"? Auth check returned: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Auth test error: {e}")

def check_potential_issues():
    """Check for common issues that prevent project visibility"""
    print("\n=== Checking Potential Issues ===")
    
    issues = []
    
    # Issue 1: OPA server down
    try:
        response = requests.get("http://localhost:8181/health", timeout=2)
        if response.status_code != 200:
            issues.append("OPA server not healthy")
        else:
            print("✓ OPA server is healthy")
    except:
        issues.append("Cannot reach OPA server")
    
    # Issue 2: Wrong user email in OPA policy
    try:
        payload = {"input": {"user": "hellf0rg0d@proton.me"}}
        response = requests.post(
            "http://localhost:8181/v1/data/organization/rbac/user_projects",
            json=payload,
            timeout=2
        )
        if response.status_code == 200:
            result = response.json()
            projects = result.get('result', [])
            if 'project_B' in projects:
                print("✓ OPA returns project_B for hellf0rg0d@proton.me")
            else:
                issues.append(f"OPA doesn't return project_B, got: {projects}")
        else:
            issues.append(f"OPA policy error: {response.status_code}")
    except Exception as e:
        issues.append(f"OPA test failed: {e}")
    
    # Issue 3: Project ID mapping
    name_to_id = {"project_B": 30}
    if name_to_id.get("project_B") == 30:
        print("✓ Project name mapping is correct (project_B → 30)")
    else:
        issues.append("Project name mapping incorrect")
    
    if issues:
        print("\n❌ Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ No obvious issues detected")
    
    return len(issues) == 0

def suggest_debugging_steps():
    """Suggest next debugging steps"""
    print("\n=== Debugging Suggestions ===")
    
    print("1. Check if project ID 30 exists in database:")
    print("   - Log into Label Studio as admin/superuser")
    print("   - Check if project ID 30 is visible to admin")
    print("   - If not visible to admin, project doesn't exist")
    
    print("\n2. Check if OPA integration is active:")
    print("   - Add debug logging to opa_integration.py")
    print("   - Check Django logs when hellf0rg0d@proton.me logs in")
    print("   - Verify get_user_accessible_projects() is being called")
    
    print("\n3. Check user session:")
    print("   - Clear browser cache/cookies")
    print("   - Log out and log back in as hellf0rg0d@proton.me")
    print("   - Check if user is in correct organization")
    
    print("\n4. Check Django manager integration:")
    print("   - Verify ProjectManager.for_user() is being used in views")
    print("   - Check if superuser bypass is working correctly")
    print("   - Test with different user roles")

def main():
    """Run complete debugging suite"""
    print("Label Studio Project Visibility Debug")
    print("=" * 50)
    
    test_project_existence()
    test_opa_integration_in_label_studio()
    test_user_authentication()
    no_issues = check_potential_issues()
    suggest_debugging_steps()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("- OPA integration works at API level")
    print("- hellf0rg0d@proton.me should get project ID 30")
    print("- Issue is likely in UI/session/database level")
    
    if no_issues:
        print("\n🔍 Next step: Check if project ID 30 exists in database")
    else:
        print("\n⚠️  Fix the issues above first")

if __name__ == "__main__":
    main()
