from django.urls import path
from .views import BuildingList, get_route, campus_map


urlpatterns = [
    
    path('', campus_map, name='campus-map'),
    path('<str:short_name>/', campus_map, name='campus-map-short'),
    
    #api's
    path('api/buildings/', BuildingList.as_view(), name='building-list'),
    path('api/route/', get_route, name='get-route'),
]
