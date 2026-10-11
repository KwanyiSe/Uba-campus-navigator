from django.conf import settings
from django.conf.urls.static import static
from campus.admin import campus_admin_site
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', campus_admin_site.urls),

    path("academic/", include("academic.b4_urls")),
    
    path("classes/", TemplateView.as_view(template_name="classes.html"), name="classes"),

    path("halls/", TemplateView.as_view(template_name="halls.html"), name="halls"),

    path("campus-now/", TemplateView.as_view(template_name="campus_now.html"), name="campus-now"),
    
    path("menu/", TemplateView.as_view(template_name="menu.html"), name="menu"),

    path('', include("campus.urls")),

    path("api/academic/", include("academic.urls")),

    # Accounts
    path('api/auth/', include('accounts.urls')),

    # Feedback
    path('api/feedback/', include('feedback.urls')),    #kwanyi :),,. so tireeeed today :/

    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )