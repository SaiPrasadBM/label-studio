#!/usr/bin/env python3
"""
Test Django OPA integration directly using Django's test framework
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Add the project path
sys.path.insert(0, '/home/cpu11/ant/label-studio')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'label_studio.settings.label_studio')

try:
    django.setup()
    
    # Now we can import Django models and functions
    from django.contrib.auth import get_user_model
    from django.test import TestCase, RequestFactory
    from unittest.mock import patch, Mock
    from label_studio.core.opa_integration import get_user_accessible_projects, opa_client
    from projects.models import Project
    from organizations.models import Organization
    
    User = get_user_model()
    
    def test_opa_integration_directly():
        """Test OPA integration functions directly"""
        print("=== Testing OPA Integration Functions ===")
        
        # Create test organization and user
        try:
            org = Organization.objects.get_or_create(title='Test Org')[0]
            user = User.objects.get_or_create(
                username='hellf0rg0d',
                email='hellf0rg0d@proton.me',
                defaults={'password': 'testpass123'}
            )[0]
            user.active_organization = org
            user.save()
            
            print(f"✓ Created test user: {user.email}")
            
            # Test OPA client directly
            with patch('label_studio.core.opa_integration.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'result': ['project_B']}
                mock_response.raise_for_status.return_value = None
                mock_post.return_value = mock_response
                
                projects = opa_client.get_user_projects('hellf0rg0d@proton.me')
                print(f"✓ OPA client returned: {projects}")
                
                if 30 in projects:
                    print("✅ Project ID 30 is accessible via OPA client")
                else:
                    print("❌ Project ID 30 is NOT accessible via OPA client")
            
            # Test helper function
            with patch('label_studio.core.opa_integration.opa_client.get_user_projects') as mock_opa:
                mock_opa.return_value = [30]
                
                accessible_projects = get_user_accessible_projects(user)
                print(f"✓ Helper function returned: {accessible_projects}")
                
                if 30 in accessible_projects:
                    print("✅ Project ID 30 is accessible via helper function")
                else:
                    print("❌ Project ID 30 is NOT accessible via helper function")
            
            return True
            
        except Exception as e:
            print(f"✗ Django integration test failed: {e}")
            return False
    
    def test_project_manager_filtering():
        """Test ProjectManager filtering"""
        print("\n=== Testing ProjectManager Filtering ===")
        
        try:
            # Get or create organization and user
            org = Organization.objects.get_or_create(title='Test Org')[0]
            user = User.objects.get_or_create(
                username='hellf0rg0d',
                email='hellf0rg0d@proton.me',
                defaults={'password': 'testpass123'}
            )[0]
            user.active_organization = org
            user.save()
            
            # Create test projects
            project30 = Project.objects.get_or_create(
                id=30,
                defaults={'title': 'Project B', 'organization': org}
            )[0]
            project41 = Project.objects.get_or_create(
                id=41,
                defaults={'title': 'Project A', 'organization': org}
            )[0]
            
            print(f"✓ Created test projects: {project30.id}, {project41.id}")
            
            # Test ProjectManager.for_user with mocked OPA
            with patch('label_studio.core.opa_integration.get_user_accessible_projects') as mock_get_projects:
                mock_get_projects.return_value = [30]  # Only project 30 accessible
                
                accessible_projects = Project.objects.for_user(user)
                project_ids = list(accessible_projects.values_list('id', flat=True))
                
                print(f"✓ ProjectManager.for_user returned IDs: {project_ids}")
                
                if 30 in project_ids:
                    print("✅ Project ID 30 is accessible via ProjectManager")
                else:
                    print("❌ Project ID 30 is NOT accessible via ProjectManager")
                
                if 41 not in project_ids:
                    print("✅ Project ID 41 is correctly filtered out")
                else:
                    print("❌ Project ID 41 should be filtered out but isn't")
            
            return True
            
        except Exception as e:
            print(f"✗ ProjectManager test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def main():
        """Run all Django integration tests"""
        print("Django OPA Integration Tests")
        print("=" * 50)
        
        success1 = test_opa_integration_directly()
        success2 = test_project_manager_filtering()
        
        print("\n" + "=" * 50)
        if success1 and success2:
            print("✅ All Django integration tests passed!")
        else:
            print("❌ Some Django integration tests failed!")
        
        return success1 and success2
    
    if __name__ == "__main__":
        main()
        
except Exception as e:
    print(f"Failed to setup Django: {e}")
    import traceback
    traceback.print_exc()
