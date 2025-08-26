from rest_framework.permissions import SAFE_METHODS, BasePermission
from organizations.roles import is_org_admin


class HasObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.has_permission(request.user)


class MemberHasOwnerPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS and not request.user.own_organization:
            return False

        return obj.has_permission(request.user)


class IsOrgAdmin(BasePermission):
    """Allow only organization admins (owner or admin) of the user's active org."""

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        org = getattr(user, 'active_organization', None) if user else None
        return bool(user and user.is_authenticated and is_org_admin(user, org))


class IsOrgMember(BasePermission):
    """Allow only active organization members."""

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        org = getattr(user, 'active_organization', None) if user else None
        return bool(user and user.is_authenticated and org and org.has_permission(user))


class IsOrgOwner(BasePermission):
    """Allow only the owner (creator) of the active organization."""

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        org = getattr(user, 'active_organization', None) if user else None
        return bool(user and user.is_authenticated and org and org.created_by_id == user.id)
