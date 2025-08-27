from django.urls import path

from .views import (
    ProjectMembersAssignmentAPI,
    ProjectMembersEnableAPI,
    TaskAssignLocksAPI,
    TaskAssignSingleAPI,
    ProjectActiveAssignmentsAPI,
)

app_name = 'ee_assignments'

urlpatterns = [
    # Project members
    path('projects/<int:project_id>/members/assign', ProjectMembersAssignmentAPI.as_view(), name='project-members-assign'),
    path('projects/<int:project_id>/members/enable', ProjectMembersEnableAPI.as_view(), name='project-members-enable'),
    # Task assignment via locks
    path('projects/<int:project_id>/tasks/assign', TaskAssignLocksAPI.as_view(), name='tasks-assign'),
    path('projects/<int:project_id>/tasks/<int:task_id>/assign', TaskAssignSingleAPI.as_view(), name='task-assign-single'),
    # Active assignments listing
    path('projects/<int:project_id>/assignments/active', ProjectActiveAssignmentsAPI.as_view(), name='assignments-active'),
]
