from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include

from campus.admin import campus_admin_site
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Custom campus administration site
    path("admin/", campus_admin_site.urls),

    # Server-rendered frontend pages
    path("", include("users.urls")),

    # Campus map and campus APIs
    path("", include("campus.urls")),

    # Accounts REST API
    path("api/auth/", include("accounts.urls")),

    # Feedback REST API
    path("api/feedback/", include("feedback.urls")),

    # Academic / campus activity APIs
    path("api/academic/", include("academic.urls")),

    # JWT authentication for API clients / future React frontend
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
