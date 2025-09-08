#!/usr/bin/env python3
"""
Script to check if project ID 30 exists and create it if it doesn't
"""

import os
import sys
import django
import json

# Add the project path
sys.path.insert(0, '/home/cpu11/ant/label-studio')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'label_studio.settings.label_studio')

def check_and_create_project():
    """Check if project ID 30 exists and create it if needed"""
    try:
        # Setup Django
        django.setup()
        
        # Import models after Django setup
        from projects.models import Project
        from organizations.models import Organization
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        print("=== Checking Project ID 30 ===")
        
        # Check if project 30 exists
        try:
            project = Project.objects.get(id=30)
            print(f"✓ Project ID 30 exists: '{project.title}'")
            print(f"  Organization: {project.organization.title}")
            print(f"  Created: {project.created_at}")
            return project
        except Project.DoesNotExist:
            print("❌ Project ID 30 does NOT exist")
            
            # Create the project
            print("\n=== Creating Project ID 30 ===")
            
            # Get or create a default organization
            org, created = Organization.objects.get_or_create(
                title='Default Organization',
                defaults={'created_by_id': 1}  # Assuming admin user ID 1 exists
            )
            
            if created:
                print(f"✓ Created organization: {org.title}")
            else:
                print(f"✓ Using existing organization: {org.title}")
            
            # Create the project with specific ID
            project = Project(
                id=30,
                title='Project B',
                description='Project B for OPA integration testing',
                organization=org,
                created_by_id=1,  # Assuming admin user exists
                label_config='<View><Text name="text" value="$text"/><Choices name="sentiment" toName="text"><Choice value="positive"/><Choice value="negative"/><Choice value="neutral"/></Choices></View>'
            )
            
            try:
                project.save()
                print(f"✅ Successfully created project ID 30: '{project.title}'")
                print(f"   Organization: {project.organization.title}")
                return project
            except Exception as e:
                print(f"❌ Failed to create project: {e}")
                return None
                
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def verify_project_access():
    """Verify that the project can be accessed via OPA integration"""
    print("\n=== Verifying Project Access ===")
    
    # Test OPA response
    import requests
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
            print(f"✓ OPA returns projects for hellf0rg0d@proton.me: {projects}")
            
            if 'project_B' in projects:
                print("✓ project_B is accessible via OPA")
                
                # Test conversion
                name_to_id_mapping = {"project_B": 30}
                project_id = name_to_id_mapping.get("project_B")
                print(f"✓ project_B maps to ID: {project_id}")
                
                return True
            else:
                print("❌ project_B is NOT in OPA response")
                return False
        else:
            print(f"❌ OPA error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ OPA test failed: {e}")
        return False

def main():
    """Main function"""
    print("Project ID 30 Check and Creation Script")
    print("=" * 50)
    
    # Check and create project
    project = check_and_create_project()
    
    if project:
        # Verify OPA access
        opa_works = verify_project_access()
        
        print("\n" + "=" * 50)
        print("SUMMARY:")
        print(f"✅ Project ID 30 exists: '{project.title}'")
        
        if opa_works:
            print("✅ OPA integration should work correctly")
            print("✅ hellf0rg0d@proton.me should now see project ID 30")
        else:
            print("⚠️  OPA integration may have issues")
        
        print("\nNext steps:")
        print("1. Restart Label Studio server")
        print("2. Log in as hellf0rg0d@proton.me")
        print("3. Check if project ID 30 is now visible")
        print("4. Look for [OPA DEBUG] messages in server logs")
        
    else:
        print("\n❌ Failed to create project ID 30")
        print("Check the errors above and try again")

if __name__ == "__main__":
    main()
