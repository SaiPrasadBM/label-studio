"""
Tests for OPA integration in Django managers
"""
from unittest.mock import patch, Mock
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.db import models

from projects.models import Project, ProjectManager
from tasks.models import Task
from organizations.models import Organization
from data_manager.managers import TaskManager, PreparedTaskManager
from data_manager.prepare_params import PrepareParams

User = get_user_model()


class ProjectManagerOPATestCase(TestCase):
    """Test ProjectManager OPA integration"""
    
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
        self.superuser.active_organization = self.organization
        self.superuser.save()
        
        # Create test projects
        self.project1 = Project.objects.create(
            title='Project 1',
            organization=self.organization
        )
        self.project2 = Project.objects.create(
            title='Project 2', 
            organization=self.organization
        )
        self.project3 = Project.objects.create(
            title='Project 3',
            organization=self.organization
        )
    
    @patch('core.opa_integration.filter_queryset_by_user_projects')
    def test_project_manager_for_user_calls_opa_filter(self, mock_filter):
        """Test that ProjectManager.for_user() calls OPA filtering"""
        mock_filter.return_value = Project.objects.filter(id__in=[self.project1.id, self.project2.id])
        
        result = Project.objects.for_user(self.user)
        
        # Verify OPA filter was called
        mock_filter.assert_called_once()
        args, kwargs = mock_filter.call_args
        self.assertEqual(args[1], self.user)  # User should be passed
    
    @patch('core.opa_integration.get_user_accessible_projects')
    def test_project_manager_for_user_normal_user(self, mock_get_projects):
        """Test ProjectManager.for_user() with normal user"""
        mock_get_projects.return_value = [self.project1.id, self.project2.id]
        
        result = Project.objects.for_user(self.user)
        accessible_ids = list(result.values_list('id', flat=True))
        
        self.assertIn(self.project1.id, accessible_ids)
        self.assertIn(self.project2.id, accessible_ids)
        self.assertNotIn(self.project3.id, accessible_ids)
    
    @patch('core.opa_integration.get_user_accessible_projects')
    def test_project_manager_for_user_superuser(self, mock_get_projects):
        """Test ProjectManager.for_user() with superuser"""
        mock_get_projects.return_value = None  # Superuser gets None
        
        result = Project.objects.for_user(self.superuser)
        
        # Superuser should see all projects in their organization
        self.assertEqual(result.count(), 3)
    
    @patch('core.opa_integration.get_user_accessible_projects')
    def test_project_manager_for_user_no_access(self, mock_get_projects):
        """Test ProjectManager.for_user() when user has no access"""
        mock_get_projects.return_value = []
        
        result = Project.objects.for_user(self.user)
        
        self.assertEqual(result.count(), 0)


class TaskManagerOPATestCase(TestCase):
    """Test TaskManager OPA integration"""
    
    def setUp(self):
        self.organization = Organization.objects.create(title='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.user.active_organization = self.organization
        self.user.save()
        
        # Create test projects and tasks
        self.project1 = Project.objects.create(
            title='Project 1',
            organization=self.organization
        )
        self.project2 = Project.objects.create(
            title='Project 2',
            organization=self.organization
        )
        
        with patch('label_studio.core.opa_integration.opa_client.get_user_projects') as mock_opa:
            mock_opa.return_value = [1, 2]  # User has access to projects 1 and 2 (converted from project_A, project_B)
            self.task1 = Task.objects.create(
                project=self.project1,
                data={'text': 'Task 1'}
            )
            self.task2 = Task.objects.create(
                project=self.project2,
                data={'text': 'Task 2'}
            )
    
    @patch('label_studio.core.opa_integration.get_user_accessible_projects')
    def test_task_manager_for_user_filters_by_project(self, mock_get_projects):
        """Test TaskManager.for_user() filters tasks by accessible projects"""
        mock_get_projects.return_value = [self.project1.id]
        
        result = Task.objects.for_user(self.user)
        task_ids = list(result.values_list('id', flat=True))
        
        self.assertIn(self.task1.id, task_ids)
        self.assertNotIn(self.task2.id, task_ids)


class PreparedTaskManagerOPATestCase(TestCase):
    """Test PreparedTaskManager OPA integration"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.organization = Organization.objects.create(title='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.user.active_organization = self.organization
        self.user.save()
        
        # Create test project and tasks
        self.project = Project.objects.create(
            title='Test Project',
            organization=self.organization
        )
        
        self.task1 = Task.objects.create(
            project=self.project,
            data={'text': 'Task 1'}
        )
        self.task2 = Task.objects.create(
            project=self.project,
            data={'text': 'Task 2'}
        )
    
    @patch('core.opa_integration.get_user_accessible_projects')
    def test_prepared_task_manager_only_filtered_with_authenticated_user(self, mock_get_projects):
        """Test PreparedTaskManager.only_filtered() with authenticated user"""
        mock_get_projects.return_value = [self.project.id]
        
        # Create mock request with authenticated user
        request = self.factory.get('/')
        request.user = self.user
        
        prepare_params = PrepareParams(
            project=self.project.id,
            request=request
        )
        
        manager = PreparedTaskManager()
        manager.model = Task
        result = manager.only_filtered(prepare_params)
        
        # Should call OPA filtering
        mock_get_projects.assert_called_once_with(self.user)
    
    def test_prepared_task_manager_only_filtered_without_user(self):
        """Test PreparedTaskManager.only_filtered() without authenticated user"""
        # Create mock request without user
        request = self.factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        
        prepare_params = PrepareParams(
            project=self.project.id,
            request=request
        )
        
        manager = PreparedTaskManager()
        manager.model = Task
        
        # Should not raise an error even without authenticated user
        result = manager.only_filtered(prepare_params)
        self.assertIsNotNone(result)


class OPAManagerIntegrationTestCase(TestCase):
    """Integration tests for OPA manager functionality"""
    
    def setUp(self):
        self.organization1 = Organization.objects.create(title='Org 1')
        self.organization2 = Organization.objects.create(title='Org 2')
        
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com'
        )
        self.user1.active_organization = self.organization1
        self.user1.save()
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com'
        )
        self.user2.active_organization = self.organization2
        self.user2.save()
        
        # Create projects in different organizations
        self.project1_org1 = Project.objects.create(
            title='Project 1 Org 1',
            organization=self.organization1
        )
        self.project2_org1 = Project.objects.create(
            title='Project 2 Org 1',
            organization=self.organization1
        )
        self.project1_org2 = Project.objects.create(
            title='Project 1 Org 2',
            organization=self.organization2
        )
    
    @patch('core.opa_integration.get_user_accessible_projects')
    def test_organization_and_opa_filtering_combined(self, mock_get_projects):
        """Test that both organization and OPA filtering work together"""
        # User1 should only see project1_org1 via OPA, even though they're in org1
        mock_get_projects.return_value = [self.project1_org1.id]
        
        result = Project.objects.for_user(self.user1)
        accessible_ids = list(result.values_list('id', flat=True))
        
        # Should only see project1_org1 (organization filter + OPA filter)
        self.assertEqual(len(accessible_ids), 1)
        self.assertIn(self.project1_org1.id, accessible_ids)
        self.assertNotIn(self.project2_org1.id, accessible_ids)  # Same org, but OPA says no
        self.assertNotIn(self.project1_org2.id, accessible_ids)  # Different org
    
    @patch('core.opa_integration.get_user_accessible_projects')
    def test_cross_organization_opa_access_blocked(self, mock_get_projects):
        """Test that OPA cannot grant access to projects in different organizations"""
        # Even if OPA says user1 can access project in org2, organization filter should block it
        mock_get_projects.return_value = [self.project1_org1.id, self.project1_org2.id]
        
        result = Project.objects.for_user(self.user1)
        accessible_ids = list(result.values_list('id', flat=True))
        
        # Should only see project from their own organization
        self.assertEqual(len(accessible_ids), 1)
        self.assertIn(self.project1_org1.id, accessible_ids)
        self.assertNotIn(self.project1_org2.id, accessible_ids)  # Different org, blocked by organization filter
