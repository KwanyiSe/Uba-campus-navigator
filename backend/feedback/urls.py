from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_feedback, name='create_feedback'),
    path('list/', views.list_feedback, name='list_feedback'),
    path('admin/', views.admin_feedback, name='admin_feedback'),
]
