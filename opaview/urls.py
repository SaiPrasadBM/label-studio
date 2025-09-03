from django.urls import path
from . import views

app_name = 'opaview'

urlpatterns = [
    # Add your URL patterns here
    path('', views.index, name='index'),
]
