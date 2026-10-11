from django.urls import path
from .views import BuildingList, get_route, campus_map

urlpatterns = [
    path("map/", campus_map, name="campus-map"),
    path("api/buildings/", BuildingList.as_view(), name="building-list"),
    path("api/route/", get_route, name="get-route"),
    # Keep this catch-all LAST so it cannot shadow named frontend routes.
    path("<str:short_name>/", campus_map, name="campus-map-short"),
]
