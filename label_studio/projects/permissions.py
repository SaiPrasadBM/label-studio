from rest_framework.permissions import BasePermission
from organizations.roles import can_import_data


class ProjectImportPermission(BasePermission):
    """
    Checks if the user has access to the project import API
    Default case is always true
    """

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        org = getattr(user, 'active_organization', None) if user else None
        return bool(user and user.is_authenticated and can_import_data(user, org))
