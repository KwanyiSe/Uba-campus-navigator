from django.urls import path

from .views import (
    RegisterView,
    ProfileView,
    ProfileUpdateView,
    UniversityListView,
    SchoolListView,
    DepartmentListView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),

    path(
        "universities/",
        UniversityListView.as_view(),
        name="universities"),

    path(
        "schools/",
        SchoolListView.as_view(),
        name="schools"),

    path(
        "departments/",
        DepartmentListView.as_view(),
        name="departments"),
    
    path(
    "profile/update/",
    ProfileUpdateView.as_view(),
    name="profile-update"
    ),
]