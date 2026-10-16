from django.shortcuts import render, get_object_or_404
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
from django.utils.cache import patch_vary_headers
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
    cache_timeout = 300

    def get_queryset(self):
        qs = Building.objects.select_related("university").all()
        uni_short = (self.request.query_params.get("university") or "").strip()
        if uni_short:
            qs = qs.filter(university__short_name__iexact=uni_short)
        return qs.order_by("id")

    def list(self, request, *args, **kwargs):
        # The serializer may return absolute media URLs, so include the host in
        # the cache key. A version token lets model signals invalidate all old
        # building payloads without flushing unrelated route-cache entries.
        uni_short = (request.query_params.get("university") or "").strip().casefold()
        version = cache.get("campus:building_cache_version", 1)
        cache_key = f"campus:buildings:v{version}:{request.get_host().lower()}:{uni_short or 'all'}"
        payload = cache.get(cache_key)
        if payload is None:
            queryset = self.filter_queryset(self.get_queryset())
            payload = self.get_serializer(queryset, many=True).data
            # Store plain JSON-compatible data, not a DRF Response object.
            payload = list(payload)
            cache.set(cache_key, payload, self.cache_timeout)
        response = Response(payload)
        patch_vary_headers(response, ("Host",))
        response["Cache-Control"] = "public, max-age=60"
        return response

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
        # Logged-in users stay scoped to their own university.
        # Guests fall back to the first active university.
        profile = getattr(request.user, "profile", None) if request.user.is_authenticated else None
        university = (
            profile.university
            if profile and profile.university and profile.university.active
            else University.objects.filter(active=True).first()
        )

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

    # Splash branding: use the user's school logo when available,
    # otherwise the university logo, otherwise the UNIMAP logo in the template.
    splash_logo_url = None
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        school = getattr(profile, "school", None) if profile else None
        if school and getattr(school, "logo", None):
            try:
                if school.logo:
                    splash_logo_url = school.logo.url
            except ValueError:
                splash_logo_url = None

    if not splash_logo_url and getattr(university, "logo", None):
        try:
            if university.logo:
                splash_logo_url = university.logo.url
        except ValueError:
            splash_logo_url = None

    # Pass JSON to template
    context = {
        "university": university,
        "profile": getattr(request.user, "profile", None) if request.user.is_authenticated else None,
        "campus_boundary_json": json.dumps(campus_boundary),
        "splash_logo_url": splash_logo_url,
        "show_unimap_splash": request.session.pop("show_unimap_splash", False),
    }

    return render(request, "campus_map.html", context)


# Route API
@api_view(["GET"])
def get_route(request):
    start = request.GET.get("start")  # "lat,lng"
    end = request.GET.get("end")      # "lat,lng"

    if not start or not end:
        return Response({"error": "start and end parameters required"}, status=400)

    try:
        start_lat, start_lng = map(float, start.split(","))
        end_lat, end_lng = map(float, end.split(","))
        values = (start_lat, start_lng, end_lat, end_lng)
        if not all(-90 <= values[i] <= 90 for i in (0, 2)) or not all(-180 <= values[i] <= 180 for i in (1, 3)):
            return Response({"error": "Coordinates are outside valid latitude/longitude ranges."}, status=400)
        # GPS readings with tiny floating-point differences should reuse a route.
        normalized = tuple(round(value, 5) for value in values)
        cache_key = "route:v2:" + ":".join(f"{value:.5f}" for value in normalized)
        cached = cache.get(cache_key)
        if cached is not None:
            response = Response(cached)
            response["Cache-Control"] = "private, max-age=60"
            return response

        start_lat, start_lng, end_lat, end_lng = normalized
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

        ors_response = requests.post(ORS_URL, json=payload, headers=headers, timeout=(4, 12))
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

        cache.set(cache_key, result, 600)  # successful route results only; 10 minutes
        response = Response(result)
        response["Cache-Control"] = "private, max-age=60"
        return response

    except (TypeError, ValueError):
        return Response({"error": "Coordinates must be supplied as lat,lng pairs."}, status=400)
    except requests.RequestException:
        return Response({"error": "The routing service is temporarily unavailable. Please try again."}, status=502)
    except (KeyError, IndexError, TypeError, ValueError):
        return Response({"error": "The routing service returned an invalid route."}, status=502)


# Helper
def format_duration(seconds: float):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds} sec"
    minutes = seconds // 60
    remaining = seconds % 60
    return f"{minutes} min" if remaining == 0 else f"{minutes} min {remaining} sec"
