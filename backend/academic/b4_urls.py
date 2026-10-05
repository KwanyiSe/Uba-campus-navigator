from django.urls import path

from academic.b4_views import class_detail

app_name = "b4"

urlpatterns = [
    path(
        "class-detail/<int:session_id>/",
        class_detail,
        name="class-detail",
    ),
]
