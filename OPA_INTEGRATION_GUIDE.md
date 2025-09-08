# OPA Integration for Label Studio

This guide explains how to integrate Open Policy Agent (OPA) with Label Studio for fine-grained project access control.

## Overview

The OPA integration provides global project filtering throughout Label Studio, ensuring users can only access projects they have permission to view according to OPA policies. All database queries are automatically filtered at the manager level.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Label Studio  │    │       OPA       │    │   Policy Data   │
│                 │    │                 │    │                 │
│  ┌───────────┐  │    │  ┌───────────┐  │    │  ┌───────────┐  │
│  │ Manager   │──┼────┼─▶│  Policy   │──┼────┼─▶│   Rules   │  │
│  │ Layer     │  │    │  │ Engine    │  │    │  │   & Data  │  │
│  └───────────┘  │    │  └───────────┘  │    │  └───────────┘  │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Features

- **Global Filtering**: All project and task queries automatically filtered
- **Caching**: 5-minute cache to reduce OPA server load
- **Security**: Fail-closed security model (deny access if OPA unavailable)
- **Performance**: Minimal overhead with efficient caching
- **Superuser Support**: Bypass OPA filtering for superusers
- **Multi-Organization**: Works with Label Studio's organization model

## Installation & Configuration

### 1. Django Settings

Add the following to your Django settings:

```python
# OPA Configuration
OPA_URL = 'http://localhost:8181'  # OPA server URL
OPA_TIMEOUT = 5  # Request timeout in seconds
OPA_CACHE_TIMEOUT = 300  # Cache timeout in seconds (5 minutes)

# Add to INSTALLED_APPS if not already present
INSTALLED_APPS = [
    # ... other apps
    'core',
]
```

### 2. OPA Server Setup

Start OPA server with the required policy:

```bash
# Start OPA server
opa run --server --addr localhost:8181 policy.rego data.json
```

### 3. Policy Configuration

Create `policy.rego`:

```rego
package organization.rbac

# Five-tier role hierarchy: Owner > Administrator > Manager > Reviewer > Annotator

# User role assignments
user_org_roles := {
    "user_alice": "Owner",
    "user_bob": "Administrator", 
    "user_diana": "Manager",
    "user_frank": "Reviewer",
    "user_grace": "Annotator"
}

# Project assignments per user
resource_assignments := {
    "user_diana": {
        "projects": ["project_A", "project_B"]
    },
    "user_frank": {
        "projects": ["project_A"]
    },
    "user_grace": {
        "projects": ["project_B", "project_C"]
    }
}

# Main rule to get projects accessible to a user
user_projects := projects if {
    # Privileged users (Owner/Admin) get all projects
    is_privileged(input.user)
    projects := all_projects
} else := projects if {
    # Other users get only assigned projects
    projects := resource_assignments[input.user].projects
} else := [] # Default to empty if no assignments
```

### 4. Project Name to ID Mapping

Since the existing policy returns project names (e.g., "project_A", "project_B"), you need to configure the mapping in `opa_integration.py`:

```python
# In _convert_project_names_to_ids method
name_to_id_mapping = {
    "project_A": 1,
    "project_B": 2, 
    "project_C": 3,
    # Add your actual project mappings here
}
```

The policy works with the existing five-tier RBAC system where:
- **Owners/Administrators**: Get access to all projects
- **Managers**: Get access to assigned projects in their workspaces
- **Reviewers/Annotators**: Get access to specifically assigned projects
        },
        "admin@example.com": {
            "role": "admin",
            "projects": []
        }
    },
    "all_projects": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
}
```

## API Endpoints

### Get User Projects
```http
GET /api/opa/user-projects/
Authorization: Bearer <token>
```

Response:
```json
{
    "project_ids": [1, 2, 3],
    "is_superuser": false
}
```

### Clear User Cache
```http
POST /api/opa/clear-cache/
Authorization: Bearer <token>
```

Response:
```json
{
    "message": "Cache cleared successfully"
}
```

## Management Commands

### Clear OPA Cache

Clear cache for specific user:
```bash
python manage.py clear_opa_cache --user user@example.com
```

Clear cache for all users:
```bash
python manage.py clear_opa_cache --all
```

## How It Works

### 1. Manager Integration

The integration modifies Django managers to automatically filter queries:

- `ProjectManager.for_user()` - Filters projects by OPA permissions
- `TaskManager.for_user()` - Filters tasks by accessible projects
- `PreparedTaskManager.only_filtered()` - Applies filtering in data manager

### 2. Request Flow

```
1. User makes request
2. Manager calls OPA integration
3. Check cache for user's projects
4. If not cached, query OPA server
5. Cache result for 5 minutes
6. Filter queryset by allowed projects
7. Return filtered results
```

### 3. OPA Request Format

```http
POST http://localhost:8181/v1/data/organization/rbac/user_projects
Content-Type: application/json

{
    "input": {
        "user": "user@example.com"
    }
}
```

Expected OPA Response:
```json
{
    "result": [1, 2, 3]
}
```

## Security Considerations

### Fail-Closed Security
- If OPA server is unreachable, users get **no access** (secure default)
- Only superusers bypass OPA filtering
- Organization-level filtering is always applied first

### Cache Security
- Cache keys include user email for isolation
- Cache automatically expires after configured timeout
- Manual cache clearing available via API and management command

### Cross-Organization Protection
- Users cannot access projects from other organizations
- OPA permissions are applied **after** organization filtering
- Even if OPA grants access, organization boundaries are respected

## Monitoring & Debugging

### Logging

Enable debug logging in Django settings:

```python
LOGGING = {
    'loggers': {
        'core.opa_integration': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

### Health Checks

Monitor OPA integration health:

```python
from core.opa_integration import opa_client

try:
    projects = opa_client.get_user_projects('test@example.com')
    print("OPA integration healthy")
except Exception as e:
    print(f"OPA integration error: {e}")
```

## Testing

Run the comprehensive test suite:

```bash
# Test OPA integration
python manage.py test tests.test_opa_integration

# Test manager integration  
python manage.py test tests.test_opa_managers
```

## Troubleshooting

### Common Issues

1. **OPA Server Unreachable**
   - Check OPA server is running on configured URL
   - Verify network connectivity
   - Check firewall settings

2. **Empty Project Lists**
   - Verify OPA policy is correct
   - Check data.json contains user mappings
   - Ensure policy path matches request URL

3. **Performance Issues**
   - Increase cache timeout
   - Monitor OPA server performance
   - Check for excessive cache clearing

### Debug Steps

1. Check OPA server directly:
   ```bash
   curl -X POST http://localhost:8181/v1/data/organization/rbac/user_projects \
     -H "Content-Type: application/json" \
     -d '{"input": {"user": "test@example.com"}}'
   ```

2. Clear cache and retry:
   ```bash
   python manage.py clear_opa_cache --user test@example.com
   ```

3. Check Django logs for OPA integration errors

## Performance Optimization

### Caching Strategy
- Default 5-minute cache balances performance and freshness
- Adjust `OPA_CACHE_TIMEOUT` based on your needs
- Consider Redis for distributed caching in multi-server setups

### OPA Server Optimization
- Use OPA's built-in caching features
- Deploy OPA close to Label Studio servers
- Monitor OPA server resource usage

## Migration Guide

### From Existing Installations

1. Deploy OPA server with policies
2. Add OPA configuration to Django settings
3. Test with a subset of users first
4. Monitor logs during rollout
5. Gradually enable for all users

### Rollback Plan

To disable OPA integration:

1. Remove OPA configuration from Django settings
2. The managers will fall back to organization-only filtering
3. No data migration required

## Example Policies

### Role-Based Access
```rego
package organization.rbac

user_projects = project_ids {
    input.user
    user_data := data.users[input.user]
    user_data.role == "project_manager"
    project_ids := user_data.managed_projects
}

user_projects = project_ids {
    input.user
    user_data := data.users[input.user]
    user_data.role == "annotator"
    project_ids := user_data.assigned_projects
}
```

### Department-Based Access
```rego
package organization.rbac

user_projects = project_ids {
    input.user
    user_data := data.users[input.user]
    department := user_data.department
    project_ids := data.department_projects[department]
}
```

### Time-Based Access
```rego
package organization.rbac

user_projects = project_ids {
    input.user
    user_data := data.users[input.user]
    now := time.now_ns()
    user_data.access_start <= now
    now <= user_data.access_end
    project_ids := user_data.projects
}
```

## Support

For issues and questions:
- Check the troubleshooting section above
- Review Django and OPA logs
- Test OPA policies independently
- Verify network connectivity between services
