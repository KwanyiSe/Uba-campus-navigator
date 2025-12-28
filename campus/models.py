from django.db import models

# Creating models for our campus

class Building(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    category = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to="buildings/photos/", blank=True, null=True)
    icon = models.ImageField(upload_to="buildings/icons/", blank=True, null=True)
    
    def __str__(self):
        return self.name
    
