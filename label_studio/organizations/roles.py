"""Simple role helpers without DB schema changes.

Coarse roles are inferred as:
- OWNER: user == organization.created_by
- ADMIN: Django is_superuser or is_staff (optional admin ability)
- MEMBER: default for other users in the organization

Fine-grained roles (scaffolded, not persisted):
- EDITOR: can configure projects, manage tasks/exports, manage webhooks/storage
- ANNOTATOR: can view and annotate tasks
- VIEWER: can only view

These helpers provide a consistent API to check capabilities without DB changes.
"""
from __future__ import annotations
from typing import Literal, Optional, Dict, Set

from django.conf import settings

Role = Literal["OWNER", "ADMIN", "MEMBER"]
FineRole = Literal["EDITOR", "ANNOTATOR", "VIEWER"]


def get_user_role_for_org(user, organization) -> Role:
    if user is None or not user.is_authenticated or organization is None:
        return "MEMBER"

    # Owner
    if organization.created_by_id == user.id:
        return "OWNER"

    # System-level admin (Django admin)
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return "ADMIN"

    # Otherwise a regular member
    return "MEMBER"


def is_org_admin(user, organization) -> bool:
    role = get_user_role_for_org(user, organization)
    return role in ("OWNER", "ADMIN")


def can_manage_projects(user, organization) -> bool:
    # For now, only admins (incl. owner) can manage projects
    return is_org_admin(user, organization)


def can_import_data(user, organization) -> bool:
    # Example capability: restrict imports to admins
    return is_org_admin(user, organization)


def can_annotate(user, organization) -> bool:
    # Everyone who is a member of the active organization can annotate
    if organization is None:
        return False
    return organization.has_permission(user)


# ----- Fine-grained role scaffolding -----

def get_fine_grained_role(user, organization) -> FineRole:
    """Infer a fine-grained role from org membership without DB changes.

    - EDITOR: org admins (OWNER/ADMIN)
    - ANNOTATOR: org member with permission
    - VIEWER: authenticated but no org membership (or anonymous -> VIEWER False access)
    """
    if user is None or not getattr(user, "is_authenticated", False):
        return "VIEWER"

    if is_org_admin(user, organization):
        return "EDITOR"

    if organization is not None and organization.has_permission(user):
        return "ANNOTATOR"

    return "VIEWER"


# Capability map for clarity and potential future expansion
ROLE_CAPABILITIES: Dict[FineRole, Set[str]] = {
    "EDITOR": {
        "view_project",
        "annotate",
        "export",
        "manage_project_settings",
        "manage_tasks",
        "manage_webhooks",
        "manage_storages",
        "manage_members",
    },
    "ANNOTATOR": {
        "view_project",
        "annotate",
        "export",  # many orgs allow annotators to export; adjust if needed
    },
    "VIEWER": {
        "view_project",
    },
}


def has_capability(user, organization, capability: str) -> bool:
    role = get_fine_grained_role(user, organization)
    return capability in ROLE_CAPABILITIES.get(role, set())


# Convenience wrappers
def can_view_project(user, organization) -> bool:
    return has_capability(user, organization, "view_project")


def can_manage_project_settings(user, organization) -> bool:
    return has_capability(user, organization, "manage_project_settings")


def can_manage_tasks(user, organization) -> bool:
    return has_capability(user, organization, "manage_tasks")


def can_manage_webhooks(user, organization) -> bool:
    return has_capability(user, organization, "manage_webhooks")


def can_manage_storages(user, organization) -> bool:
    return has_capability(user, organization, "manage_storages")


def can_manage_members(user, organization) -> bool:
    return has_capability(user, organization, "manage_members")
