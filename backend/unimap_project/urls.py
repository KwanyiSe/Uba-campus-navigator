from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', campus_admin_site.urls),  # replacing default admin

    path('', include("campus.urls")),
    path('', include('users.urls')),

    # Accounts
    path('api/auth/', include('accounts.urls')),

    # Feedback
    path('api/feedback/', include('feedback.urls')),

    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )