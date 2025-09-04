"""
Core API endpoints for OPA integration
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core.opa_integration import opa_client, get_user_accessible_projects

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_projects(request):
    """
    Get projects accessible to the current user via OPA
    """
    try:
        project_ids = get_user_accessible_projects(request.user)
        return Response({
            'project_ids': project_ids,
            'is_superuser': request.user.is_superuser
        })
    except Exception as e:
        logger.error(f"Error fetching user projects: {str(e)}")
        return Response(
            {'error': 'Unable to fetch accessible projects'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_user_cache(request):
    """
    Clear OPA cache for the current user
    """
    try:
        opa_client.clear_user_cache(request.user.email)
        return Response({'message': 'Cache cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing user cache: {str(e)}")
        return Response(
            {'error': 'Unable to clear cache'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
