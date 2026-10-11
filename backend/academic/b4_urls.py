from django.urls import path
from django.views.generic import TemplateView
from academic.b4_views import class_detail

app_name = "b4"

urlpatterns = [
    path("class-detail/<int:session_id>/", class_detail, name="class-detail", ),

    path("my-classes/", TemplateView.as_view(template_name="academic/my_classes.html"), name="my-classes"),
]
