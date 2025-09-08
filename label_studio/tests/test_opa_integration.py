"""
Tests for OPA integration functionality
"""
import json
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APITestCase
from rest_framework import status
import requests

from core.opa_integration import OPAClient, get_user_accessible_projects, filter_queryset_by_user_projects
from projects.models import Project
from organizations.models import Organization

User = get_user_model()


class OPAClientTestCase(TestCase):
    """Test cases for OPAClient"""
    
    def setUp(self):
        self.opa_client = OPAClient()
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    @patch('label_studio.core.opa_integration.requests.post')
    def test_get_user_projects_success(self, mock_post):
        """Test successful retrieval of user projects"""
        # Mock OPA response with project names (as per existing policy)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': ['project_A', 'project_B', 'project_C']}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test
        projects = self.opa_client.get_user_projects('test@example.com')
        
        # Assertions - should convert project names to IDs
        self.assertEqual(projects, [1, 2, 3])
        mock_post.assert_called_once_with(
            'http://localhost:8181/v1/data/organization/rbac/user_projects',
            json={'input': {'user': 'test@example.com'}},
            timeout=5
        )
    
    @patch('label_studio.core.opa_integration.requests.post')
    def test_get_user_projects_cached(self, mock_post):
        """Test that results are cached properly"""
        # Mock OPA response with project names
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': ['project_A', 'project_B']}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # First call
        projects1 = self.opa_client.get_user_projects('test@example.com')
        
        # Second call - should use cache
        projects2 = self.opa_client.get_user_projects('test@example.com')
        
        # Assertions
        self.assertEqual(projects1, [1, 2])
        self.assertEqual(projects2, [1, 2])
        # Should only call OPA once due to caching
        mock_post.assert_called_once()
    
    @patch('label_studio.core.opa_integration.requests.post')
    def test_get_user_projects_opa_error(self, mock_post):
        """Test handling of OPA server errors"""
        mock_post.side_effect = requests.exceptions.RequestException("Connection failed")
        
        # Should return empty list on error (fail-closed)
        projects = self.opa_client.get_user_projects('test@example.com')
        self.assertEqual(projects, [])
    
    @patch('label_studio.core.opa_integration.requests.post')
    def test_get_user_projects_empty_result(self, mock_post):
        """Test handling of empty OPA response"""
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        projects = self.opa_client.get_user_projects('test@example.com')
        
        self.assertEqual(projects, [])
    
    def test_clear_user_cache(self):
        """Test cache clearing functionality"""
        # Set some cached data
        cache.set('opa_user_projects:test@example.com', [1, 2, 3], 300)
        
        # Verify it's cached
        self.assertEqual(cache.get('opa_user_projects:test@example.com'), [1, 2, 3])
        
        # Clear cache
        self.opa_client.clear_user_cache('test@example.com')
        
        # Verify it's cleared
        self.assertIsNone(cache.get('opa_user_projects:test@example.com'))


class OPAIntegrationFunctionsTestCase(TestCase):
    """Test cases for OPA integration helper functions"""
    
    def setUp(self):
        self.organization = Organization.objects.create(title='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.user.active_organization = self.organization
        self.user.save()
        
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    @patch('core.opa_integration.opa_client.get_user_projects')
    def test_get_user_accessible_projects_normal_user(self, mock_get_projects):
        """Test project access for normal user"""
        mock_get_projects.return_value = [1, 2, 3]
        
        projects = get_user_accessible_projects(self.user)
        
        self.assertEqual(projects, [1, 2, 3])
        mock_get_projects.assert_called_once_with('test@example.com')
    
    def test_get_user_accessible_projects_superuser(self):
        """Test project access for superuser"""
        projects = get_user_accessible_projects(self.superuser)
        
        self.assertIsNone(projects)  # Superusers get None (all access)
    
    @patch('core.opa_integration.opa_client.get_user_projects')
    def test_get_user_accessible_projects_no_email(self, mock_get_projects):
        """Test project access for user without email"""
        self.user.email = ''
        self.user.save()
        
        projects = get_user_accessible_projects(self.user)
        
        self.assertEqual(projects, [])
        mock_get_projects.assert_not_called()
    
    @patch('core.opa_integration.get_user_accessible_projects')
    def test_filter_queryset_by_user_projects_normal_user(self, mock_get_projects):
        """Test queryset filtering for normal user"""
        mock_get_projects.return_value = [1, 2]
        
        # Create test projects
        project1 = Project.objects.create(title='Project 1', organization=self.organization)
        project2 = Project.objects.create(title='Project 2', organization=self.organization)
        project3 = Project.objects.create(title='Project 3', organization=self.organization)
        
        # Mock the project IDs to match what OPA returns
        project1.id = 1
        project2.id = 2
        project3.id = 3
        project1.save()
        project2.save()
        project3.save()
        
        queryset = Project.objects.all()
        filtered_queryset = filter_queryset_by_user_projects(queryset, self.user)
        
        # Should only include projects 1 and 2
        filtered_ids = list(filtered_queryset.values_list('id', flat=True))
        self.assertIn(1, filtered_ids)
        self.assertIn(2, filtered_ids)
        self.assertNotIn(3, filtered_ids)
    
    @patch('core.opa_integration.get_user_accessible_projects')
    def test_filter_queryset_by_user_projects_superuser(self, mock_get_projects):
        """Test queryset filtering for superuser"""
        mock_get_projects.return_value = None
        
        # Create test projects
        Project.objects.create(title='Project 1', organization=self.organization)
        Project.objects.create(title='Project 2', organization=self.organization)
        
        queryset = Project.objects.all()
        filtered_queryset = filter_queryset_by_user_projects(queryset, self.superuser)
        
        # Should return all projects for superuser
        self.assertEqual(queryset.count(), filtered_queryset.count())
    
    @patch('core.opa_integration.get_user_accessible_projects')
    def test_filter_queryset_by_user_projects_no_access(self, mock_get_projects):
        """Test queryset filtering when user has no project access"""
        mock_get_projects.return_value = []
        
        # Create test projects
        Project.objects.create(title='Project 1', organization=self.organization)
        Project.objects.create(title='Project 2', organization=self.organization)
        
        queryset = Project.objects.all()
        filtered_queryset = filter_queryset_by_user_projects(queryset, self.user)
        
        # Should return empty queryset
        self.assertEqual(filtered_queryset.count(), 0)


class OPAAPITestCase(APITestCase):
    """Test cases for OPA API endpoints"""
    
    def setUp(self):
        self.organization = Organization.objects.create(title='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.user.active_organization = self.organization
        self.user.save()
        
        cache.clear()
    
    def tearDown(self):
        cache.clear()
    
    @patch('core.opa_integration.get_user_accessible_projects')
    def test_user_projects_endpoint(self, mock_get_projects):
        """Test the user projects API endpoint"""
        mock_get_projects.return_value = [1, 2, 3]
        
        self.client.force_authenticate(user=self.user)
        # Skip this test since we haven't set up URL routing yet
        self.skipTest("API endpoints not configured in URL routing yet")
    
    def test_user_projects_endpoint_unauthenticated(self):
        """Test the user projects API endpoint without authentication"""
        # Skip this test since we haven't set up URL routing yet
        self.skipTest("API endpoints not configured in URL routing yet")
    
    @patch('core.opa_integration.opa_client.clear_user_cache')
    def test_clear_cache_endpoint(self, mock_clear_cache):
        """Test the clear cache API endpoint"""
        # Skip this test since we haven't set up URL routing yet
        self.skipTest("API endpoints not configured in URL routing yet")
    
    def test_clear_cache_endpoint_unauthenticated(self):
        """Test the clear cache API endpoint without authentication"""
        # Skip this test since we haven't set up URL routing yet
        self.skipTest("API endpoints not configured in URL routing yet")


@override_settings(
    OPA_URL='http://test-opa:8181',
    OPA_TIMEOUT=10,
    OPA_CACHE_TIMEOUT=600
)
class OPASettingsTestCase(TestCase):
    """Test OPA client with custom settings"""
    
    def test_custom_settings(self):
        """Test that OPA client respects custom settings"""
        client = OPAClient()
        
        self.assertEqual(client.base_url, 'http://test-opa:8181')
        self.assertEqual(client.timeout, 10)
        self.assertEqual(client.cache_timeout, 600)
