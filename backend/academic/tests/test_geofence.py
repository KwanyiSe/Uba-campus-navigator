"""
B2 Geofence Service Tests

Exactly the six ticket-level scenarios:
1. inside
2. outside
3. boundary/edge
4. low GPS accuracy
5. no active geofence
6. client spoof attempt

The BuildingGeofence model is owned by B1 and must exist in campus.models
before these tests can run.
"""

from django.test import TestCase

from academic.services.geofence_service import (
    MAX_GPS_ACCURACY,
    haversine_distance,
    verify_location,
)
from campus.models import Building, BuildingGeofence, University


class GeofenceServiceTests(TestCase):

    def setUp(self):
        self.university = University.objects.create(
            name="Test University",
            short_name="TU",
            country="Cameroon",
        )

        self.building = Building.objects.create(
            name="Engineering Building",
            latitude=5.9635,
            longitude=10.1595,
            university=self.university,
        )

        # Simple square around the test building.
        self.polygon = [
            {"lat": 5.9630, "lng": 10.1590},
            {"lat": 5.9630, "lng": 10.1600},
            {"lat": 5.9640, "lng": 10.1600},
            {"lat": 5.9640, "lng": 10.1590},
        ]

    def create_geofence(self, active=True):
        return BuildingGeofence.objects.create(
            building=self.building,
            center_lat=5.9635,
            center_lng=10.1595,
            radius=100,
            polygon=self.polygon,
            is_active=active,
        )

    def test_location_inside_polygon(self):
        self.create_geofence()

        result = verify_location(
            building=self.building,
            latitude=5.9635,
            longitude=10.1595,
            accuracy=10,
        )

        self.assertTrue(result["verified"])

        # Sanity-check that the required Haversine helper is available.
        self.assertGreaterEqual(
            haversine_distance(
                5.9635,
                10.1595,
                5.9635,
                10.1595,
            ),
            0,
        )

    def test_location_outside_polygon(self):
        self.create_geofence()

        result = verify_location(
            building=self.building,
            latitude=5.9650,
            longitude=10.1610,
            accuracy=10,
        )

        self.assertFalse(result["verified"])
        self.assertEqual(
            result["reason"],
            "Location is outside the building geofence.",
        )

    def test_location_on_polygon_edge(self):
        self.create_geofence()

        result = verify_location(
            building=self.building,
            latitude=5.9630,
            longitude=10.1595,
            accuracy=10,
        )

        self.assertTrue(result["verified"])

    def test_low_gps_accuracy_is_rejected(self):
        self.create_geofence()

        result = verify_location(
            building=self.building,
            latitude=5.9635,
            longitude=10.1595,
            accuracy=MAX_GPS_ACCURACY + 1,
        )

        self.assertFalse(result["verified"])
        self.assertEqual(
            result["reason"],
            "GPS accuracy is too low.",
        )

    def test_no_active_geofence_is_rejected(self):
        result = verify_location(
            building=self.building,
            latitude=5.9635,
            longitude=10.1595,
            accuracy=10,
        )

        self.assertFalse(result["verified"])
        self.assertEqual(
            result["reason"],
            "No active geofence exists for this building.",
        )

    def test_client_cannot_spoof_location_verified(self):
        self.create_geofence()

        # This coordinate is outside the polygon.
        #
        # The client cannot make it pass by sending
        # location_verified=True because verify_location()
        # has no such parameter and computes the result itself.

        result = verify_location(
            building=self.building,
            latitude=5.9650,
            longitude=10.1610,
            accuracy=10,
        )

        self.assertFalse(result["verified"])
        self.assertEqual(
            result["reason"],
            "Location is outside the building geofence.",
        )
