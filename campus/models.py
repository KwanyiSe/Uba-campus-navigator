from django.db import models

# Creating models for our campus


class Building(models.Model):
    """
        
        stores building informations
    
    """
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    category = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to="buildings/photos/", blank=True, null=True)
    icon = models.ImageField(upload_to="buildings/icons/", blank=True, null=True)
    
    def __str__(self):
        return self.name
    

class SiteVisit(models.Model):
    """
    Stores one record per unique browser session.
    We use Django's session_key as a proxy for a unique visitor.
    """

    # Unique browser session identifier
    session_key = models.CharField(max_length=40, unique=True)

    # When the visitor first appeared on the site
    first_visit = models.DateTimeField(auto_now_add=True)

    # Updated automatically on every request
    last_visit = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.session_key


class DailyStats(models.Model):
    """
    Stores aggregated visitor counts per day.
    This prevents numbers from dropping due to session expiry.
    """

    date = models.DateField(unique=True)
    visitors = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.date)
