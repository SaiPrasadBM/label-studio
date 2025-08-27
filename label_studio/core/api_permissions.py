from rest_framework.permissions import SAFE_METHODS, BasePermission
from organizations.roles import (
    is_org_admin,
    is_org_maintainer,
    is_org_supervisor,
    is_org_worker,
    can_manage_storages,
    can_invite_members,
    can_modify_member_roles,
    can_manage_jobs,
    can_assign_jobs_tasks_projects,
)


class HasObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.has_permission(request.user)


class MemberHasOwnerPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS and not request.user.own_organization:
            return False

        return obj.has_permission(request.user)


class IsOrgAdmin(BasePermission):
    """Allow only organization admins (owner or maintainer) of the user's active org."""

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


class IsOrgMaintainer(BasePermission):
    """Allow OWNER or MAINTAINER of the active organization."""

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        org = getattr(user, 'active_organization', None) if user else None
        return bool(user and user.is_authenticated and is_org_maintainer(user, org))


class IsOrgSupervisorOrAbove(BasePermission):
    """Allow OWNER, MAINTAINER, or SUPERVISOR of the active organization."""

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        org = getattr(user, 'active_organization', None) if user else None
        return bool(user and user.is_authenticated and is_org_supervisor(user, org))


class IsOrgWorkerOrAbove(BasePermission):
    """Allow any member: OWNER, MAINTAINER, SUPERVISOR, or WORKER of the active organization."""

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        org = getattr(user, 'active_organization', None) if user else None
        return bool(user and user.is_authenticated and is_org_worker(user, org))


class CanManageStorages(BasePermission):
    """Allow only members who can manage storages."""

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        org = getattr(user, 'active_organization', None) if user else None
        return bool(user and user.is_authenticated and can_manage_storages(user, org))


class CanInviteMembers(BasePermission):
    """Allow only members who can invite other members."""

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        org = getattr(user, 'active_organization', None) if user else None
        return bool(user and user.is_authenticated and can_invite_members(user, org))


class CanModifyMemberRoles(BasePermission):
    """Allow only members who can modify other members' roles or remove members."""

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        org = getattr(user, 'active_organization', None) if user else None
        return bool(user and user.is_authenticated and can_modify_member_roles(user, org))


class CanManageJobs(BasePermission):
    """Allow only members who can manage jobs (task/job lifecycle)."""

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        org = getattr(user, 'active_organization', None) if user else None
        return bool(user and user.is_authenticated and can_manage_jobs(user, org))


class CanAssignJobsTasksProjects(BasePermission):
    """Allow only members who can assign jobs/tasks/projects (supervisors and above)."""

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        org = getattr(user, 'active_organization', None) if user else None
        return bool(user and user.is_authenticated and can_assign_jobs_tasks_projects(user, org))
