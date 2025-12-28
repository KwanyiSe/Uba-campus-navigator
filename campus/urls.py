from django.urls import path
from .views import BuildingList, campus_map_page, get_route


urlpatterns = [
    path("", campus_map_page, name="campus-map"),
    path("api/buildings/", BuildingList.as_view(), name="building-list"),
    path("api/route/", get_route, name="route_to_building"),
]

