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
        Get list of project IDs that the user has access to from OPA.
        
        Args:
            user_email (str): Email of the user
            
        Returns:
            list: List of project IDs the user can access
        """
        print(f"[OPA DEBUG] Getting projects for user: {user_email}")
        cache_key = f"opa_user_projects:{user_email}"
        
        # Try to get from cache first
        cached_projects = cache.get(cache_key)
        if cached_projects is not None:
            print(f"[OPA DEBUG] Found cached projects for {user_email}: {cached_projects}")
            return cached_projects
            
        try:
            # Make request to OPA using the existing policy structure
            print(f"[OPA DEBUG] Making OPA request to {self.base_url}")
            response = requests.post(
                f"{self.base_url}/v1/data/organization/rbac/user_projects",
                json={"input": {"user": user_email}},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Extract project list from response
            data = response.json()
            projects = data.get('result', [])
            print(f"[OPA DEBUG] OPA returned projects: {projects}")
            
            # Convert project names to IDs if needed (assuming project names map to IDs)
            # The existing policy returns project names like ["project_A", "project_B"]
            # We need to convert these to numeric IDs that Label Studio uses
            project_ids = self._convert_project_names_to_ids(projects)
            print(f"[OPA DEBUG] Converted to project IDs: {project_ids}")
            
            # Cache the result
            cache.set(cache_key, project_ids, self.cache_timeout)
            
            return project_ids
            
        except Exception as e:
            # Log error and return empty list (fail-closed)
            print(f"[OPA DEBUG] OPA request failed for user {user_email}: {e}")
            return []
    
    def _convert_project_names_to_ids(self, project_names):
        """
        Convert project names from OPA policy to Label Studio project IDs.
        This is a mapping function that should be customized based on your setup.
        
        Args:
            project_names (list): List of project names from OPA
            
        Returns:
            list: List of project IDs
        """
        # Example mapping - customize this based on your project naming convention
        name_to_id_mapping = {
            "project_A": 41,
            "project_B": 30, 
            "project_C": 25,
            # Add more mappings as needed
        }
        
        project_ids = []
        for name in project_names:
            if isinstance(name, str) and name in name_to_id_mapping:
                project_ids.append(name_to_id_mapping[name])
            elif isinstance(name, (int, str)) and str(name).isdigit():
                # If it's already a numeric ID, use it directly
                project_ids.append(int(name))
        
        return project_ids
    
    def clear_user_cache(self, user_email):
        """Clear cached project data for a user"""
        cache_key = f"opa_user_projects:{user_email}"
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
    print(f"[OPA DEBUG] get_user_accessible_projects called for user: {user.email}")
    
    # Superusers bypass OPA filtering
    if user.is_superuser:
        print(f"[OPA DEBUG] User {user.email} is superuser, bypassing OPA")
        return None  # None means no filtering
    
    accessible_projects = opa_client.get_user_projects(user.email)
    print(f"[OPA DEBUG] Final accessible projects for {user.email}: {accessible_projects}")
    return accessible_projects


def filter_queryset_by_user_projects(queryset, user, project_field='id'):
    """
    Filter a queryset to only include projects the user has access to
    
    Args:
        queryset: Django QuerySet to filter
        user: Django User instance
        project_field: Field name that contains the project ID (default: 'id')
        
    Returns:
        Filtered QuerySet
    """
    print(f"[OPA DEBUG] filter_queryset_by_user_projects called for user: {user.email}, field: {project_field}")
    
    # Get accessible project IDs
    accessible_projects = get_user_accessible_projects(user)
    
    # If None (superuser), don't filter
    if accessible_projects is None:
        print(f"[OPA DEBUG] No filtering applied (superuser)")
        return queryset
    
    # Filter by accessible projects
    filter_kwargs = {f"{project_field}__in": accessible_projects}
    print(f"[OPA DEBUG] Applying filter: {filter_kwargs}")
    filtered_queryset = queryset.filter(**filter_kwargs)
    print(f"[OPA DEBUG] Queryset filtered, count before: {queryset.count()}, after: {filtered_queryset.count()}")
    return filtered_queryset
