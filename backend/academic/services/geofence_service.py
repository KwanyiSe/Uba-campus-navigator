"""
B2 Geofence Service
-------------------

Server-side location verification for the attendance system.

Responsibilities:
- Validate GPS coordinates and GPS accuracy.
- Find the active BuildingGeofence for a building.
- Verify a GPS point against the building polygon using ray casting.
- Treat polygon boundaries as inside.
- Never trust a client-provided `location_verified` value.

B2 deliberately does NOT handle:
- student authentication
- enrollment/eligibility
- creating AttendanceRecord objects
Those belong to the attendance API/integration layer (B3).
"""

import math
from django.conf import settings
from campus.models import BuildingGeofence

MAX_GPS_ACCURACY = getattr(settings, "MAX_GPS_ACCURACY", 100.0,)

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Return the great-circle distance between two GPS coordinates in metres.
    """

    earth_radius = 6_371_000.0

    lat1 = math.radians(float(lat1))
    lat2 = math.radians(float(lat2))
    delta_lat = math.radians(float(lat2) - float(lat1))
    delta_lon = math.radians(float(lon2) - float(lon1))

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    # Protect against tiny floating-point overshoots.
    a = max(0.0, min(1.0, a))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


def _point_on_segment(latitude, longitude, start, end):
    """
    Return True when the point lies on a polygon edge.

    A small tolerance is used because GPS coordinates are floating-point
    values.
    """

    x = longitude
    y = latitude

    x1 = float(start["lng"])
    y1 = float(start["lat"])
    x2 = float(end["lng"])
    y2 = float(end["lat"])

    cross_product = (
        (y - y1) * (x2 - x1)
        - (x - x1) * (y2 - y1)
    )

    if abs(cross_product) > 1e-10:
        return False

    return (
        min(x1, x2) <= x <= max(x1, x2)
        and min(y1, y2) <= y <= max(y1, y2)
    )


def _point_in_polygon(latitude, longitude, polygon):
    """
    Ray-casting point-in-polygon algorithm.

    Expected polygon format:
        [
            {"lat": 5.9630, "lng": 10.1590},
            {"lat": 5.9630, "lng": 10.1600},
            {"lat": 5.9640, "lng": 10.1600},
            {"lat": 5.9640, "lng": 10.1590},
        ]

    The polygon does not need to repeat its first point at the end.
    Points on the boundary are considered inside.
    """

    if not isinstance(polygon, list) or len(polygon) < 3:
        return False

    try:
        for point in polygon:
            if not isinstance(point, dict):
                return False
            if "lat" not in point or "lng" not in point:
                return False
            if not math.isfinite(float(point["lat"])):
                return False
            if not math.isfinite(float(point["lng"])):
                return False
    except (TypeError, ValueError):
        return False

    inside = False
    previous = polygon[-1]

    for current in polygon:
        if _point_on_segment(
            latitude,
            longitude,
            previous,
            current,
        ):
            return True

        current_lat = float(current["lat"])
        current_lng = float(current["lng"])
        previous_lat = float(previous["lat"])
        previous_lng = float(previous["lng"])

        # The two comparisons deliberately use opposite sides of the
        # horizontal ray to avoid double-counting polygon vertices.
        intersects = (
            (current_lat > latitude) != (previous_lat > latitude)
            and longitude
            < (
                (previous_lng - current_lng)
                * (latitude - current_lat)
                / (previous_lat - current_lat)
                + current_lng
            )
        )

        if intersects:
            inside = not inside

        previous = current

    return inside


def verify_location(building, latitude, longitude, accuracy):
    """
    Verify a GPS reading against a building's active polygon geofence.

    Parameters:
        building: campus.models.Building instance
        latitude: reported GPS latitude
        longitude: reported GPS longitude
        accuracy: reported GPS accuracy in metres

    Returns:
        {
            "verified": bool,
            "reason": str,
        }

    Security note:
        This function has no `location_verified` parameter. A client cannot
        force the verification result by sending location_verified=True.
    """

    if accuracy is None:
        return {
            "verified": False,
            "reason": "GPS accuracy is required.",
        }

    try:
        latitude = float(latitude)
        longitude = float(longitude)
        accuracy = float(accuracy)
    except (TypeError, ValueError):
        return {
            "verified": False,
            "reason": "Invalid GPS data.",
        }

    if not (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and math.isfinite(accuracy)
    ):
        return {
            "verified": False,
            "reason": "Invalid GPS data.",
        }

    if accuracy < 0:
        return {
            "verified": False,
            "reason": "Invalid GPS accuracy.",
        }

    if accuracy > MAX_GPS_ACCURACY:
        return {
            "verified": False,
            "reason": "GPS accuracy is too low.",
        }

    if not -90 <= latitude <= 90:
        return {
            "verified": False,
            "reason": "Invalid latitude.",
        }

    if not -180 <= longitude <= 180:
        return {
            "verified": False,
            "reason": "Invalid longitude.",
        }

    try:
        geofence = BuildingGeofence.objects.get(
            building=building,
            is_active=True,
        )
    except BuildingGeofence.DoesNotExist:
        return {
            "verified": False,
            "reason": "No active geofence exists for this building.",
        }
    except BuildingGeofence.MultipleObjectsReturned:
        return {
            "verified": False,
            "reason": "Multiple geofences found for this building.",
        }

    polygon = geofence.polygon

    if not _point_in_polygon(
        latitude,
        longitude,
        polygon,
    ):
        return {
            "verified": False,
            "reason": "Location is outside the building geofence.",
            "accuracy": accuracy,
        }

    distance = haversine_distance(
        latitude,
        longitude,
        geofence.center_lat,
        geofence.center_lng,
    )

    return {
        "verified": True,
        "reason": "Location verified successfully.",
        "accuracy": accuracy,
        "distance_from_center": round(distance, 2),
    }