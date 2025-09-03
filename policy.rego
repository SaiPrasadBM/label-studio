# OPA Policy for a Five-Tier Role-Based Access Control (RBAC) System
#
# This policy defines five roles (Owner, Administrator, Manager, Reviewer, Annotator)
# and enforces a detailed permission matrix for various actions within an organization.

package organization.rbac

# --- Mock Data ---
# In a real-world scenario, this data would be provided as input from your application.

# User roles at the organization level
user_org_roles := {
    "user_alice": "Owner",
    "user_bob": "Administrator",
    "user_charlie": "Administrator",
    "user_diana": "Manager",
    "user_eve": "Manager",
    "user_frank": "Reviewer",
    "user_grace": "Annotator",
    "testing@example.com":"Annotator",
    "user_heidi": "Annotator",
}

# Workspace and Project assignments for users
# Managers, Reviewers, and Annotators must be assigned to specific resources.
resource_assignments := {
    # Diana is a Manager for workspace_1 and its projects
    "user_diana": {
        "workspaces": ["workspace_1"],
        "projects": ["project_A", "project_B"],
    },
    # Eve is a Manager for workspace_2
    "user_eve": {
        "workspaces": ["workspace_2"],
        "projects": ["project_C"],
    },
    # Frank is a Reviewer for tasks in project_A
    "user_frank": {
        "projects": ["project_A"],
    },
    # Grace is an Annotator for tasks in project_B and project_C
    "user_grace": {
        "projects": ["project_B"],
    },
   # testing@example.com is a Annotator for tasks in project_A,project_B and project_c
    "testing@example.com": {
	"projects": ["project_A", "project_B", "project_C"]
    },
    # Heidi is an Annotator for tasks in project_A
    "user_heidi": {
        "projects": ["project_A"],
    },
}

# Project settings, e.g., if annotators can view their own data
project_settings := {
    "project_A": {"annotator_can_view_own_data": true},
    "project_B": {"annotator_can_view_own_data": false},
    "project_C": {"annotator_can_view_own_data": true},
}

# --- Default Deny ---
# By default, all actions are denied unless explicitly allowed by a rule.
default allow = false

# --- Helper Rules ---

# Get the role for a given user
user_role(user) = role if {
    role := user_org_roles[user]
}

# Check if a user has a specific role
is_owner(user) if { user_role(user) == "Owner" }
is_admin(user) if { user_role(user) == "Administrator" }
is_manager(user) if { user_role(user) == "Manager" }
is_reviewer(user) if { user_role(user) == "Reviewer" }
is_annotator(user) if { user_role(user) == "Annotator" }

# Check if a user has a role of at least a certain level
is_at_least_manager(user) if {
    ur := user_role(user)
    ur == "Owner"; ur == "Administrator"; ur == "Manager"
}

is_at_least_reviewer(user) if {
    is_at_least_manager(user); is_reviewer(user)
}

# Check if a user is assigned to a specific workspace
is_assigned_to_workspace(user, workspace) if {
    resource_assignments[user].workspaces[_] == workspace
}

# Check if a user is assigned to a specific project
is_assigned_to_project(user, project) if {
    resource_assignments[user].projects[_] == project
}


# --- Permission Policies ---

# Policy: Billing Access
allow if {
    input.action == "access_billing"
    is_owner(input.user)
}

# Policy: User Management Permissions
allow if {
    input.action == "invite_user"
    is_owner(input.user)
}
allow if {
    input.action == "invite_user"
    is_admin(input.user)
}
allow if {
    input.action == "assign_role"
    is_owner(input.user)
}
allow if {
    input.action == "assign_role"
    is_admin(input.user)
}
allow if {
    input.action == "view_activity_logs"
    is_owner(input.user)
}
allow if {
    input.action == "view_activity_logs"
    is_admin(input.user)
}

# Policy: Project Management Permissions (CRUD on Workspaces)
allow if {
    # Owners and Admins have org-wide access to workspaces
    input.action in {"create_workspace", "read_workspace", "update_workspace", "delete_workspace"}
    is_owner(input.user)
}
allow if {
    input.action in {"create_workspace", "read_workspace", "update_workspace", "delete_workspace"}
    is_admin(input.user)
}
allow if {
    # Managers can manage workspaces they are assigned to
    input.action in {"read_workspace", "update_workspace", "delete_workspace"}
    is_manager(input.user)
    is_assigned_to_workspace(input.user, input.resource.workspace_id)
}

# Policy: Project Management Permissions (CRUD on Projects)
allow if {
    # Owners and Admins have org-wide access to projects
    input.action in {"create_project", "read_project", "update_project", "delete_project"}
    is_owner(input.user)
}
allow if {
    input.action in {"create_project", "read_project", "update_project", "delete_project"}
    is_admin(input.user)
}
allow if {
    # Managers can manage projects they are assigned to
    input.action in {"create_project", "read_project", "update_project", "delete_project"}
    is_manager(input.user)
    is_assigned_to_project(input.user, input.resource.project_id)
}

# Policy: Read-only access for Reviewers and Annotators to their assigned projects
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


# Policy: Save custom project templates
allow if {
    input.action == "save_project_template"
    is_at_least_manager(input.user)
}

# Policy: Data Access Controls
allow if {
    # Import/export restricted to Manager and above
    input.action in {"import_data", "export_data"}
    is_at_least_manager(input.user)
}
allow if {
    # Reviewers and above have full visibility into project data they are assigned to
    input.action == "view_project_data"
    is_at_least_reviewer(input.user)
    is_assigned_to_project(input.user, input.resource.project_id)
}
allow if {
    # Annotators can only view their own data if permitted by project settings
    input.action == "view_own_annotated_data"
    is_annotator(input.user)
    is_assigned_to_project(input.user, input.resource.project_id)
    project_settings[input.resource.project_id].annotator_can_view_own_data == true
}

# Policy: Workflow Permissions
allow if {
    # Assigning tasks
    input.action == "assign_task"
    is_at_least_manager(input.user) # Simplified: Managers and above can assign
}
allow if {
    # Accessing review workflows
    input.action == "access_review_workflow"
    is_at_least_reviewer(input.user)
    is_assigned_to_project(input.user, input.resource.project_id)
}
allow if {
    # Annotating tasks
    input.action == "annotate_task"
    is_annotator(input.user)
    is_assigned_to_project(input.user, input.resource.project_id)
}
allow if {
    # Viewing annotator performance (simplified scope)
    input.action == "view_annotator_performance"
    is_at_least_reviewer(input.user)
}
