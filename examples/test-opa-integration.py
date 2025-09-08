#!/usr/bin/env python3
"""
Test script for OPA integration with Label Studio
Run this script to verify OPA integration is working correctly
"""

import requests
import json
import time
import sys

# Configuration
OPA_URL = "http://localhost:8181"
LABEL_STUDIO_URL = "http://localhost:8080"
TEST_USER = "annotator1@example.com"

def test_opa_server():
    """Test direct OPA server connectivity"""
    print("Testing OPA server connectivity...")
    
    try:
        # Health check
        response = requests.get(f"{OPA_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ OPA server is healthy")
        else:
            print(f"✗ OPA health check failed: {response.status_code}")
            return False
            
        # Test policy endpoint
        payload = {"input": {"user": TEST_USER}}
        response = requests.post(
            f"{OPA_URL}/v1/data/organization/rbac/user_projects",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            projects = result.get('result', [])
            print(f"✓ OPA policy working - User {TEST_USER} has access to projects: {projects}")
            return True
        else:
            print(f"✗ OPA policy test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ OPA server test failed: {e}")
        return False

def test_label_studio_opa_integration():
    """Test Label Studio OPA integration endpoints"""
    print("\nTesting Label Studio OPA integration...")
    
    try:
        # Test user projects endpoint (requires authentication)
        response = requests.get(f"{LABEL_STUDIO_URL}/api/opa/user-projects/")
        
        if response.status_code == 401:
            print("✓ OPA endpoints properly require authentication")
            return True
        elif response.status_code == 404:
            print("✗ OPA endpoints not found - check URL routing")
            return False
        else:
            print(f"? Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Label Studio OPA integration test failed: {e}")
        return False

def test_different_users():
    """Test OPA responses for different users"""
    print("\nTesting different user access patterns...")
    
    test_users = [
        "admin@example.com",
        "project_manager@example.com", 
        "annotator1@example.com",
        "annotator2@example.com",
        "contractor@example.com",
        "nonexistent@example.com"
    ]
    
    for user in test_users:
        try:
            payload = {"input": {"user": user}}
            response = requests.post(
                f"{OPA_URL}/v1/data/organization/rbac/user_projects",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                projects = result.get('result', [])
                print(f"  {user}: {len(projects)} projects - {projects}")
            else:
                print(f"  {user}: Error {response.status_code}")
                
        except Exception as e:
            print(f"  {user}: Exception - {e}")

def test_performance():
    """Test OPA performance with multiple requests"""
    print("\nTesting OPA performance...")
    
    start_time = time.time()
    successful_requests = 0
    total_requests = 10
    
    for i in range(total_requests):
        try:
            payload = {"input": {"user": TEST_USER}}
            response = requests.post(
                f"{OPA_URL}/v1/data/organization/rbac/user_projects",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                successful_requests += 1
                
        except Exception:
            pass
    
    end_time = time.time()
    duration = end_time - start_time
    avg_time = duration / total_requests * 1000  # ms
    
    print(f"  Completed {successful_requests}/{total_requests} requests")
    print(f"  Average response time: {avg_time:.2f}ms")
    print(f"  Total time: {duration:.2f}s")
    
    if avg_time < 100:  # Less than 100ms is good
        print("✓ Performance is acceptable")
        return True
    else:
        print("⚠ Performance may be slow")
        return False

def main():
    """Run all tests"""
    print("OPA Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("OPA Server", test_opa_server),
        ("Label Studio Integration", test_label_studio_opa_integration),
        ("User Access Patterns", test_different_users),
        ("Performance", test_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 All tests passed! OPA integration is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
