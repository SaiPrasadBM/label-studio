import logging
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api_permissions import CanAssignJobsTasksProjects, IsOrgMaintainer
from projects.models import Project, ProjectMember
from tasks.models import Task
from django.utils.timezone import now
from users.models import User
from .serializers import (
    ProjectMembersAssignmentSerializer,
    ProjectMembersEnableSerializer,
    TaskAssignLocksSerializer,
    TaskAssignSingleSerializer,
)

logger = logging.getLogger(__name__)


class ProjectMembersAssignmentAPI(APIView):
    """
    Assign or remove users to/from a project (collaborators).

    Request JSON:
    {
      "add": [user_id, ...],
      "remove": [user_id, ...]
    }

    Response JSON:
    {
      "added": [user_id, ...],
      "removed": [user_id, ...]
    }
    """

    permission_classes = [IsAuthenticated, CanAssignJobsTasksProjects]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ee_assignments'

    def post(self, request, project_id: int):
        project = get_object_or_404(Project, pk=project_id)

        # Ensure actor belongs to the same organization
        if project.organization_id != request.user.active_organization_id:
            return Response({'detail': 'Cross-organization access denied'}, status=status.HTTP_403_FORBIDDEN)

        ser = ProjectMembersAssignmentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        add_ids = ser.validated_data.get('add', [])
        remove_ids = ser.validated_data.get('remove', [])

        added, removed = [], []

        with transaction.atomic():
            # Add collaborators
            for uid in add_ids:
                user = get_object_or_404(User, pk=uid)
                # Require same organization membership
                if not project.organization.has_user(user):
                    return Response(
                        {'detail': f'User {uid} is not a member of the organization'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                created = project.add_collaborator(user)
                if created:
                    added.append(user.id)

            # Remove collaborators
            if remove_ids:
                ProjectMember.objects.filter(project=project, user_id__in=remove_ids).delete()
                removed = list(remove_ids)

        logger.info(
            'EE_ASSIGNMENTS members_assign project_id=%s added=%s removed=%s actor_id=%s',
            project.id,
            added,
            removed,
            request.user.id,
        )

        return Response({'added': added, 'removed': removed}, status=status.HTTP_200_OK)


class ProjectMembersEnableAPI(APIView):
    """
    Enable or disable project members.

    Request JSON:
    {
      "enable": [user_id, ...],
      "disable": [user_id, ...]
    }

    Response JSON:
    {
      "enabled": [user_id, ...],
      "disabled": [user_id, ...]
    }
    """

    permission_classes = [IsAuthenticated, CanAssignJobsTasksProjects]

    def post(self, request, project_id: int):
        project = get_object_or_404(Project, pk=project_id)

        if project.organization_id != request.user.active_organization_id:
            return Response({'detail': 'Cross-organization access denied'}, status=status.HTTP_403_FORBIDDEN)

        ser = ProjectMembersEnableSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        enable_ids = ser.validated_data.get('enable', [])
        disable_ids = ser.validated_data.get('disable', [])

        enabled, disabled = [], []

        with transaction.atomic():
            if enable_ids:
                updated = (
                    ProjectMember.objects.filter(project=project, user_id__in=enable_ids).update(enabled=True)
                )
                if updated:
                    enabled = list(enable_ids)

            if disable_ids:
                updated = (
                    ProjectMember.objects.filter(project=project, user_id__in=disable_ids).update(enabled=False)
                )
                if updated:
                    disabled = list(disable_ids)

        logger.info(
            'EE_ASSIGNMENTS members_enable project_id=%s enabled=%s disabled=%s actor_id=%s',
            project.id,
            enabled,
            disabled,
            request.user.id,
        )

        return Response({'enabled': enabled, 'disabled': disabled}, status=status.HTTP_200_OK)


class TaskAssignLocksAPI(APIView):
    """
    Assign tasks to a user by creating or refreshing task locks. This acts as a reservation/assignment proxy
    using existing OSS primitives without introducing new models.

    Request JSON:
    {
      "user_id": 123,
      "task_ids": [1,2,3]
    }

    Response JSON:
    {
      "locked": [task_id, ...],
      "skipped": {task_id: reason}
    }
    """

    permission_classes = [IsAuthenticated, CanAssignJobsTasksProjects]

    def post(self, request, project_id: int):
        project = get_object_or_404(Project, pk=project_id)

        if project.organization_id != request.user.active_organization_id:
            return Response({'detail': 'Cross-organization access denied'}, status=status.HTTP_403_FORBIDDEN)

        ser = TaskAssignLocksSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user_id = ser.validated_data['user_id']
        task_ids = ser.validated_data['task_ids']

        target_user = get_object_or_404(User, pk=user_id)
        # Target user must be an org member and project collaborator
        if not project.organization.has_user(target_user):
            return Response({'detail': 'Target user not in organization'}, status=status.HTTP_400_BAD_REQUEST)
        if not project.has_collaborator(target_user):
            project.add_collaborator(target_user)

        locked, skipped = [], {}
        qs = Task.objects.filter(project=project, id__in=task_ids)
        for task in qs:
            # Respect overlap and lock semantics. set_lock will refresh or create lock if possible.
            try:
                task.set_lock(target_user)
                locked.append(task.id)
            except Exception as exc:
                skipped[str(task.id)] = str(exc)

        logger.info(
            'EE_ASSIGNMENTS tasks_assign project_id=%s user_id=%s locked=%s skipped=%s actor_id=%s',
            project.id,
            target_user.id,
            locked,
            skipped,
            request.user.id,
        )

        return Response({'locked': locked, 'skipped': skipped}, status=status.HTTP_200_OK)


class TaskAssignSingleAPI(APIView):
    """
    Convenience endpoint to assign a single task to a single user via lock mechanism.

    Path params: project_id, task_id
    Request JSON:
    { "user_id": 123 }
    """

    permission_classes = [IsAuthenticated, CanAssignJobsTasksProjects]

    def post(self, request, project_id: int, task_id: int):
        project = get_object_or_404(Project, pk=project_id)
        if project.organization_id != request.user.active_organization_id:
            return Response({'detail': 'Cross-organization access denied'}, status=status.HTTP_403_FORBIDDEN)

        ser = TaskAssignSingleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        target_user = get_object_or_404(User, pk=ser.validated_data['user_id'])
        if not project.organization.has_user(target_user):
            return Response({'detail': 'Target user not in organization'}, status=status.HTTP_400_BAD_REQUEST)
        if not project.has_collaborator(target_user):
            project.add_collaborator(target_user)

        task = get_object_or_404(Task, pk=task_id, project=project)
        try:
            task.set_lock(target_user)
            logger.info(
                'EE_ASSIGNMENTS task_assign_single project_id=%s task_id=%s user_id=%s actor_id=%s',
                project.id,
                task.id,
                target_user.id,
                request.user.id,
            )
            return Response({'locked': [task.id]}, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({'locked': [], 'skipped': {str(task.id): str(exc)}}, status=status.HTTP_200_OK)


class ProjectActiveAssignmentsAPI(APIView):
    """
    List active task assignments (non-expired TaskLocks) for a project.

    Response JSON:
    {
      "project_id": 123,
      "assignments": [
        {
          "task_id": 1,
          "task_inner_id": 10,
          "assignee": {"id": 5, "email": "user@example.com", "username": "user"},
          "expire_at": "ISO8601",
          "created_at": "ISO8601"
        }, ...
      ]
    }
    """

    permission_classes = [IsAuthenticated, IsOrgMaintainer]

    def get(self, request, project_id: int):
        project = get_object_or_404(Project, pk=project_id)

        if project.organization_id != request.user.active_organization_id:
            return Response({'detail': 'Cross-organization access denied'}, status=status.HTTP_403_FORBIDDEN)

        locks_qs = (
            project.tasks.prefetch_related('locks__user', 'locks__assigned_by')
            .values(
                'locks__id',
                'locks__expire_at',
                'locks__created_at',
                'locks__user__id',
                'locks__user__email',
                'locks__user__username',
                'locks__assigned_by__id',
                'locks__assigned_by__email',
                'locks__assigned_by__username',
                'id',
                'inner_id',
            )
        )

        assignments = []
        for row in locks_qs:
            expire_at = row['locks__expire_at']
            if not expire_at or expire_at <= now():
                continue
            assignments.append({
                'task_id': row['id'],
                'task_inner_id': row['inner_id'],
                'assignee': {
                    'id': row['locks__user__id'],
                    'email': row['locks__user__email'],
                    'username': row['locks__user__username'],
                },
                'assigned_by': {
                    'id': row['locks__assigned_by__id'],
                    'email': row['locks__assigned_by__email'],
                    'username': row['locks__assigned_by__username'],
                } if row['locks__assigned_by__id'] is not None else None,
                'expire_at': row['locks__expire_at'],
                'created_at': row['locks__created_at'],
            })

        return Response({'project_id': project.id, 'assignments': assignments}, status=status.HTTP_200_OK)
