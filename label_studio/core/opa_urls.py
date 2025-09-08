"""
URL patterns for OPA integration API endpoints
"""
from django.urls import path
from core.api import user_projects, clear_user_cache

urlpatterns = [
    path('api/opa/user-projects/', user_projects, name='opa-user-projects'),
    path('api/opa/clear-cache/', clear_user_cache, name='opa-clear-cache'),
]
