from django.conf import settings
from django.conf.urls.static import static
from campus.admin import campus_admin_site
from django.urls import path, include



urlpatterns = [
    path('admin/', campus_admin_site.urls), # replacing default admin
    path('', include("campus.urls")),
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)