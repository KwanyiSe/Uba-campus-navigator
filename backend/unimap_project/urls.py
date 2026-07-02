from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
from accounts.views import home, map_view, register_view, feedback_view
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('', home, name='home'),  # <-- Home page loads first
    path('map/', map_view, name='map'),

    path('admin/', admin.site.urls),

    # Auth - Login/Register with redirect to map
    path('login/', LoginView.as_view(template_name='login.html', next_page='map'), name='login'),
    path('register/', register_view, name='register'),
    path('logout/', include('django.contrib.auth.urls')),  # logout
    path('feedback/', feedback_view, name='feedback'),

    path('', include('users.urls')),
    path('', include("campus.urls")),

    # Accounts API
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
