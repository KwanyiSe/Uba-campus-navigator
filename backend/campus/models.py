# Creating models for our campus
from django.contrib.auth.models import User
from django.db import models



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
    photo = models.ImageField(upload_to="buildings/photos/", blank=True, null=True)
    icon = models.ImageField(upload_to="buildings/icons/", blank=True, null=True)
    
    university = models.ForeignKey(
    University,
    on_delete=models.CASCADE,
    related_name="buildings",
    null=True,
    blank=True) # remove blank after adding university to all existing buildings for migration error

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