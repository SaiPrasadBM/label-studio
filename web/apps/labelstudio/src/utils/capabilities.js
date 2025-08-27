// Map org roles to capability flags used by the UI
// org_role comes from backend `users.serializers.BaseUserSerializer.get_org_role`
// Known values: OWNER | MAINTAINER | SUPERVISOR | WORKER | null

export function getCapabilities(orgRole, fineRole, coarseRole) {
  const role = (orgRole || '').toUpperCase();

  // Default: least privileges
  const caps = {
    can_invite_members: false,
    can_modify_member_roles: false,
    can_manage_storages: false,
    can_manage_jobs: false,
    can_assign_jobs_tasks_projects: false,
  };

  switch (role) {
    case 'OWNER':
      caps.can_invite_members = true;
      caps.can_modify_member_roles = true;
      caps.can_manage_storages = true;
      caps.can_manage_jobs = true;
      caps.can_assign_jobs_tasks_projects = true;
      break;
    case 'MAINTAINER':
      caps.can_invite_members = true;
      caps.can_modify_member_roles = true;
      caps.can_manage_storages = true;
      caps.can_manage_jobs = true;
      caps.can_assign_jobs_tasks_projects = true;
      break;
    case 'SUPERVISOR':
      caps.can_manage_storages = true;
      caps.can_manage_jobs = true;
      caps.can_assign_jobs_tasks_projects = true;
      break;
    case 'WORKER':
      // No management capabilities
      break;
    default:
      // Fallback from old roles if org_role is missing
      // EDITOR roughly maps to maintainers of a project in legacy UI
      if ((fineRole || '').toUpperCase() === 'EDITOR') {
        caps.can_manage_storages = true;
        caps.can_manage_jobs = true;
        caps.can_assign_jobs_tasks_projects = true;
      }
      break;
  }

  return caps;
}
