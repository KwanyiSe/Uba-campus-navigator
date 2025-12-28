from django.contrib import admin
from .models import Building


# Registering our model here so we can ascess it in the admin panel
admin.site.register(Building)