package organization.rbac

# Default deny - users have no project access by default
default user_projects = []

# Basic user project access
user_projects = project_ids {
    input.user
    user_data := data.users[input.user]
    project_ids := user_data.projects
}

# Admin users get access to all projects
user_projects = project_ids {
    input.user
    user_data := data.users[input.user]
    user_data.role == "admin"
    project_ids := data.all_projects
}

# Project managers get access to their managed projects
user_projects = project_ids {
    input.user
    user_data := data.users[input.user]
    user_data.role == "project_manager"
    project_ids := user_data.managed_projects
}

# Department-based access
user_projects = project_ids {
    input.user
    user_data := data.users[input.user]
    department := user_data.department
    project_ids := data.department_projects[department]
}

# Time-based access (projects with expiration)
user_projects = project_ids {
    input.user
    user_data := data.users[input.user]
    now := time.now_ns()
    user_data.access_start <= now
    now <= user_data.access_end
    project_ids := user_data.temporary_projects
}

# Team-based access
user_projects = project_ids {
    input.user
    user_data := data.users[input.user]
    team := user_data.team
    project_ids := data.team_projects[team]
}
