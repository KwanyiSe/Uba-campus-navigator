from django.urls import path
from .views import RegisterView, ProfileView, UniversityListView, SchoolListView, DepartmentListView, OptionListView, SchoolOptionListView

#Kwanyise@
urlpatterns = [
 path("register/", RegisterView.as_view(), name="register"),
 path("profile/", ProfileView.as_view(), name="api-profile"),
 path("universities/", UniversityListView.as_view(), name="universities"),
 path("schools/", SchoolListView.as_view(), name="schools"),
 path("departments/", DepartmentListView.as_view(), name="departments"),
 path("options/", OptionListView.as_view(), name="options"),
 path("school-options/", SchoolOptionListView.as_view(), name="school-options"),
]
