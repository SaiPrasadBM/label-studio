"""
OPA (Open Policy Agent) integration for Label Studio
Provides global project filtering based on user permissions
"""
import logging
import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


class OPAClient:
    """Client for interacting with Open Policy Agent"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'OPA_URL', 'http://localhost:8181')
        self.timeout = getattr(settings, 'OPA_TIMEOUT', 5)
        self.cache_timeout = getattr(settings, 'OPA_CACHE_TIMEOUT', 300)  # 5 minutes
        
    def get_user_projects(self, user_email):
        """
        Fetch list of project IDs that the user has access to from OPA
        
        Args:
            user_email (str): Email of the user
            
        Returns:
            list: List of project IDs the user can access
            
        Raises:
            PermissionDenied: If OPA is unreachable or returns an error
        """
        # Check cache first
        cache_key = f"opa_user_projects_{user_email}"
        cached_projects = cache.get(cache_key)
        if cached_projects is not None:
            return cached_projects
            
        url = f"{self.base_url}/v1/data/organization/rbac/user_projects"
        
        try:
            response = requests.post(
                url,
                json={"input": {"user": user_email}},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            project_ids = result.get('result', [])
            
            # Cache the result
            cache.set(cache_key, project_ids, self.cache_timeout)
            
            return project_ids
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching projects from OPA for user {user_email}: {str(e)}")
            # Fail closed for security - no access if OPA is unreachable
            raise PermissionDenied("Unable to verify project access. Please try again later.")
    
    def clear_user_cache(self, user_email):
        """Clear cached project data for a user"""
        cache_key = f"opa_user_projects_{user_email}"
        cache.delete(cache_key)


# Global OPA client instance
opa_client = OPAClient()


def get_user_accessible_projects(user):
    """
    Get project IDs accessible to a user
    
    Args:
        user: Django User instance
        
    Returns:
        list: List of project IDs
    """
    if user.is_superuser:
        return None  # Superusers can access all projects
        
    if not hasattr(user, 'email') or not user.email:
        logger.warning(f"User {user.id} has no email address for OPA lookup")
        return []
        
    return opa_client.get_user_projects(user.email)


def filter_queryset_by_user_projects(queryset, user, project_field='id'):
    """
    Filter a queryset to only include projects the user has access to
    
    Args:
        queryset: Django QuerySet to filter
        user: Django User instance
        project_field: Field name that contains the project ID (default: 'id')
        
    Returns:
        QuerySet: Filtered queryset
    """
    project_ids = get_user_accessible_projects(user)
    
    if project_ids is None:  # Superuser
        return queryset
        
    if not project_ids:  # No access to any projects
        return queryset.none()
        
    filter_kwargs = {f'{project_field}__in': project_ids}
    return queryset.filter(**filter_kwargs)
