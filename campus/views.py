from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from .models import Building, University
from .serializers import BuildingSerializer
from unimap_project import settings
from openrouteservice import convert
import requests
import json

ORS_URL = "https://api.openrouteservice.org/v2/directions/foot-walking"


class BuildingList(generics.ListAPIView):
    """
    API endpoint to list buildings for a given university.

    Query Params:
    - university: short_name of the university (case-insensitive)

    If no university is provided, all buildings are returned.
    """

    serializer_class = BuildingSerializer

    def get_queryset(self):
        # Start with all buildings
        qs = Building.objects.all()

        # Get the 'university' parameter from the URL query string
        uni_short = self.request.GET.get("university")

        if uni_short:
            # Filter buildings by university short_name
            # __iexact → case-insensitive match
            qs = qs.filter(university__short_name__iexact=uni_short)

        return qs

# Campus map view
def campus_map(request, short_name=None):
    """
    Render campus map.
    If short_name is provided → load that university.
    If not → load first active university.
    """

    # Get university
    if short_name:
        university = get_object_or_404(
            University,
            short_name__iexact=short_name, # Use case-insensitive lookup so URLs work regardless of case
            active=True
        )
    else:
        university = University.objects.filter(active=True).first()

    # If no university exists
    if not university:
        return render(request, "campus_map.html", {
            "error": "No active university found."
        })

    # Build rectangular boundary (only if values exist)
    campus_boundary = []

    if all([
        university.min_lat,
        university.max_lat,
        university.min_lng,
        university.max_lng
    ]):
        campus_boundary = [
            [university.min_lat, university.min_lng],  # Bottom (south) → copy latitude → this is your min_lat
            [university.min_lat, university.max_lng],  # Top (north) → copy latitude → this is your max_lat
            [university.max_lat, university.max_lng],  # Right (east) → copy longitude → this is your max_lng
            [university.max_lat, university.min_lng],  # Left (west) → copy longitude → this is your min_lng
        ]

    # Pass JSON to template
    context = {
        "university": university,
        "campus_boundary_json": json.dumps(campus_boundary),
    }

    return render(request, "campus_map.html", context)


# Route API
@api_view(["GET"])
def get_route(request):
    start = request.GET.get("start")  # "lat,lng"
    end = request.GET.get("end")      # "lat,lng"

    if not start or not end:
        return Response({"error": "start and end parameters required"}, status=400)

    cache_key = f"route_{start}_{end}"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    try:
        start_lat, start_lng = map(float, start.split(","))
        end_lat, end_lng = map(float, end.split(","))

        payload = {
            "coordinates": [
                [start_lng, start_lat],
                [end_lng, end_lat]
            ]
        }

        headers = {
            "Authorization": settings.ORS_KEY,
            "Content-Type": "application/json"
        }

        ors_response = requests.post(ORS_URL, json=payload, headers=headers)
        ors_response.raise_for_status()  # auto-throws exception on non-200

        data = ors_response.json()
        if "routes" not in data or not data["routes"]:
            return Response({"error": "Invalid ORS response"}, status=500)

        route = data["routes"][0]
        decoded = convert.decode_polyline(route["geometry"])
        geometry = decoded["coordinates"]
        summary = route["summary"]

        result = {
            "coordinates": geometry,
            "distance": summary["distance"],
            "duration": format_duration(summary["duration"])
        }

        cache.set(cache_key, result, 600)  # cache 10 minutes
        return Response(result)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# Helper
def format_duration(seconds: float):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds} sec"
    minutes = seconds // 60
    remaining = seconds % 60
    return f"{minutes} min" if remaining == 0 else f"{minutes} min {remaining} sec"
