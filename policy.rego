# OPA Policy for a Five-Tier Role-Based Access Control (RBAC) System
package organization.rbac

# --- Mock Data ---
user_org_roles := {
    "user_alice": "Owner",
    "user_bob": "Administrator",
    "user_charlie": "Administrator",
    "user_diana": "Manager",
    "user_eve": "Manager",
    "user_frank": "Reviewer",
    "user_grace": "Annotator",
    "user_heidi": "Annotator",
    "testing@example.com": "Annotator",
    "hellf0rg0d@proton.me": "Annotator"
}

resource_assignments := {
    "user_diana": {
        "workspaces": ["workspace_1"],
        "projects": ["project_A", "project_B"],
    },
    "user_eve": {
        "workspaces": ["workspace_2"],
        "projects": ["project_C"],
    },
    "user_frank": {
        "projects": ["project_A"],
    },
    "user_grace": {
        "projects": ["project_B", "project_C"],
    },
    "user_heidi": {
        "projects": ["project_A"],
    },
    "testing@example.com": {
        "projects": ["project_A", "project_B", "project_C"]
    },
    "hellf0rg0d@proton.me": {
        "projects": ["project_B"]
    }
}

project_settings := {
    "project_A": {"annotator_can_view_own_data": true},
    "project_B": {"annotator_can_view_own_data": false},
    "project_C": {"annotator_can_view_own_data": true},
}

# --- Default Deny ---
default allow = false

# --- Helper Rules ---
user_role(user) = role if {
    role := user_org_roles[user]
}

is_owner(user) if { user_role(user) == "Owner" }
is_admin(user) if { user_role(user) == "Administrator" }
is_manager(user) if { user_role(user) == "Manager" }
is_reviewer(user) if { user_role(user) == "Reviewer" }
is_annotator(user) if { user_role(user) == "Annotator" }

# Helper rule to check if a user is an Owner OR an Admin
is_privileged(user) if { is_owner(user) }
is_privileged(user) if { is_admin(user) }

is_at_least_manager(user) if {
    is_privileged(user); is_manager(user)
}

is_at_least_reviewer(user) if {
    is_at_least_manager(user); is_reviewer(user)
}

is_assigned_to_workspace(user, workspace) if {
    resource_assignments[user].workspaces[_] == workspace
}

is_assigned_to_project(user, project) if {
    resource_assignments[user].projects[_] == project
}

# --- Permission Policies (Allow/Deny) ---
allow if {
    input.action == "access_billing"
    is_owner(input.user)
}

# CORRECTED: Consolidated rules for privileged users (Owner/Admin)
allow if {
    input.action in {
        "invite_user", "assign_role", "view_activity_logs",
        "create_workspace", "read_workspace", "update_workspace", "delete_workspace",
        "create_project", "read_project", "update_project", "delete_project"
    }
    is_privileged(input.user)
}

allow if {
    input.action in {"read_workspace", "update_workspace", "delete_workspace"}
    is_manager(input.user)
    is_assigned_to_workspace(input.user, input.resource.workspace_id)
}
allow if {
    input.action in {"create_project", "read_project", "update_project", "delete_project"}
    is_manager(input.user)
    is_assigned_to_project(input.user, input.resource.project_id)
}
allow if {
    input.action == "read_project"
    is_reviewer(input.user)
    is_assigned_to_project(input.user, input.resource.project_id)
}
allow if {
    input.action == "read_project"
    is_annotator(input.user)
    is_assigned_to_project(input.user, input.resource.project_id)
}
allow if {
    input.action == "save_project_template"
    is_at_least_manager(input.user)
}
allow if {
    input.action in {"import_data", "export_data"}
    is_at_least_manager(input.user)
}
allow if {
    input.action == "view_project_data"
    is_at_least_reviewer(input.user)
    is_assigned_to_project(input.user, input.resource.project_id)
}
allow if {
    input.action == "view_own_annotated_data"
    is_annotator(input.user)
    is_assigned_to_project(input.user, input.resource.project_id)
    project_settings[input.resource.project_id].annotator_can_view_own_data == true
}
allow if {
    input.action == "assign_task"
    is_at_least_manager(input.user)
}
allow if {
    input.action == "access_review_workflow"
    is_at_least_reviewer(input.user)
    is_assigned_to_project(input.user, input.resource.project_id)
}
allow if {
    input.action == "annotate_task"
    is_annotator(input.user)
    is_assigned_to_project(input.user, input.resource.project_id)
}
allow if {
    input.action == "view_annotator_performance"
    is_at_least_reviewer(input.user)
}

# --- Data Querying ---

# Helper rule to get a set of all unique project IDs that exist
all_projects[project_id] if {
    some user
    project_id := resource_assignments[user].projects[_]
}

# Main rule to get the list of projects a user can see
user_projects := projects if {
    # If the user is privileged (Owner or Admin), they can see all projects
    is_privileged(input.user)
    projects := all_projects
} else := projects if {
    # Otherwise, they see only the projects they are assigned to
    projects := resource_assignments[input.user].projects
} else := [] # Default to an empty list if no assignments exist
