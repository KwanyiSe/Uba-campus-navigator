# Creating models for our campus
from django.contrib.auth.models import User
from django.db import models


#Kwanyise@
class University(models.Model):
    """University Model allow scalability allow SaaS achitecture"""
   
    name = models.CharField(max_length=150)
    short_name = models.CharField(max_length=20)
    country = models.CharField(max_length=50)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    logo = models.ImageField(upload_to="universities/logos/", blank=True, null=True)
    #boundries
    # Bottom (south) → copy latitude → this is your min_lat
    min_lat = models.FloatField(blank=True, null=True)

    #Top (north) → copy latitude → this is your max_lat
    max_lat = models.FloatField(blank=True, null=True)

    # Left (west) → copy longitude → this is your min_lng
    min_lng = models.FloatField(blank=True, null=True)

    # Right (east) → copy longitude → this is your max_lng
    max_lng = models.FloatField(blank=True, null=True)
   
    class Meta:
        verbose_name = "University"
        verbose_name_plural = "Universities"

    def __str__(self):
        return self.name
    
    
class Building(models.Model):
    """
        stores building informations for a University
    """
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    category = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    floor = models.CharField(max_length=40, blank=True)
    capacity = models.PositiveIntegerField(blank=True, null=True)
    STATUS_CHOICES = (
        ("available", "Available"),
        ("in_use", "In Use"),
        ("limited", "Limited"),
        ("closed", "Closed"),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    opening_hours = models.CharField(max_length=120, blank=True)
    photo = models.ImageField(upload_to="buildings/photos/", blank=True, null=True)
    icon = models.ImageField(upload_to="buildings/icons/", blank=True, null=True)
    
    university = models.ForeignKey(
    University,
    on_delete=models.CASCADE,
    related_name="buildings",
    null=True,
    blank=True) #will remove blank after adding university to buildings to avoid migration errors

    def __str__(self):
        return self.name
    

class SiteVisit(models.Model):

    session_key = models.CharField(
        max_length=40,
        unique=True
    )

    first_visit = models.DateTimeField(
        auto_now_add=True
    )

    last_visit = models.DateTimeField(
        auto_now=True
    )

    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name="site_visits",
        null=True,
        blank=True
    )

    def __str__(self):
        return self.session_key
    
    
class DailyStats(models.Model):

    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name="daily_stats"
    )

    date = models.DateField()

    visitors = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("university", "date")

    def __str__(self):
        return f"{self.university.short_name} - {self.date}"
    

class CampusAdminUser(models.Model):
    # each user has exacly one CampusAdminUser profile
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="campus_admin")
    #ties that user to a specific university
    university = models.ForeignKey("University", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} ({self.university.short_name})"

# -----------------------------------------------------------------
# TEMPORARY STAND-IN for Person 1 / Ticket ATT-B1.
# This exists only so B2/B3/B4 can be tested locally before the real
# BuildingGeofence model lands. Replace with Person 1's actual model
# as soon as their branch/PR is available — do not treat this as the
# official B1 delivery.
#
# Field names match exactly what B2's geofence_service.py expects,
# per B2_README.md's documented dependency contract.
# -----------------------------------------------------------------

class BuildingGeofence(models.Model):
    building = models.OneToOneField(
        Building, on_delete=models.CASCADE, related_name="geofence"
    )
    center_lat = models.FloatField()
    center_lng = models.FloatField()
    radius = models.FloatField()
    polygon = models.JSONField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Geofence for {self.building.name}"


class GeofenceLog(models.Model):
    """
    Optional audit trail per the ticket. Deliberately does NOT store
    precise lat/lng long-term for privacy — only the computed
    distance and outcome.
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey("academic.ClassSession", on_delete=models.CASCADE)
    distance = models.FloatField(null=True, blank=True)
    success = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.session} - {'OK' if self.success else 'FAIL'}"


# Uses the real, confirmed Building model (name, latitude, longitude, university FK)
# and now links properly to academic.ClassSession since that app is installed.

class BuildingGeofence(models.Model):
    building = models.OneToOneField(
        Building,
        on_delete=models.CASCADE,
        related_name="geofence",
    )
    center_lat = models.DecimalField(max_digits=9, decimal_places=6)
    center_lng = models.DecimalField(max_digits=9, decimal_places=6)
    radius = models.PositiveIntegerField(
        help_text="Radius in meters. Suggested 120-150m for concrete buildings (GPS drift indoors)."
    )
    polygon = models.JSONField(
        blank=True,
        null=True,
        help_text="Optional list of [lat, lng] points for future ray-casting polygon check.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Building Geofence"
        verbose_name_plural = "Building Geofences"

    def __str__(self):
        return f"{self.building.name} geofence ({self.radius}m)"


class GeofenceLog(models.Model):
    """
    Audit trail only. Per privacy requirement: do NOT store precise
    student lat/lng here — only the computed distance from the geofence.
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="geofence_logs",
        null=True,
        blank=True,
    )
    session = models.ForeignKey(
        "academic.ClassSession",
        on_delete=models.CASCADE,
        related_name="geofence_logs",
        null=True,
        blank=True,
    )
    distance = models.FloatField(
        help_text="Distance from geofence center in meters at time of check."
    )
    success = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        status = "OK" if self.success else "FAILED"
        return f"{status} - {self.distance:.0f}m - {self.timestamp:%Y-%m-%d %H:%M}"
