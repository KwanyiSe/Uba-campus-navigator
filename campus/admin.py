from django.contrib.admin import AdminSite
from django.contrib import admin
from .models import Building, SiteVisit
from django.utils import timezone

#adding back our group and users since i am using a custom admin site
from django.contrib.auth.models import User, Group 
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.admin.sites import AlreadyRegistered


#creating a custom admin
class CampusAdminSite(AdminSite):
    site_header = "UBA Campus Administration"

    def index(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}

        extra_context.update(admin_index(request))

        return super().index(request, extra_context)
    
    
#instantiating CampusAdminSite class
campus_admin_site = CampusAdminSite(name="campus_admin")


#Register Django default authentication and athurization models
try:
    ''' trying to register user admin and user if they are not registered yet. '''
    campus_admin_site.register(User, UserAdmin) #making sure its not already registered
except AlreadyRegistered:
    pass

try:
    ''' trying to register group admin and group if they are not registered yet. '''    
    campus_admin_site.register(Group, GroupAdmin) 
except AlreadyRegistered:
    pass
    

#registering models

@admin.register(SiteVisit, site=campus_admin_site)
class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ("session_key", "first_visit", "last_visit")

@admin.register(Building, site=campus_admin_site)
class BuildingAdmin(admin.ModelAdmin):
    pass



def admin_index(request):
    """
    Calculates anonymous visitor statistics.

    Definitions:
    - total_visitors: all unique sessions ever seen
    - visitors_today: first-time visitors today
    - returning_visitors: visitors who first visited before today
    - only visible to superusers.
    """
    
    if not request.user.is_superuser:
        return {}

    today = timezone.now().date()

    total_visitors = SiteVisit.objects.count()

    visitors_today = SiteVisit.objects.filter(
        first_visit__date=today
    ).count()

    returning_visitors = SiteVisit.objects.filter(
        first_visit__date__lt=today
    ).count()
    
    # tracking started
    first_record = SiteVisit.objects.order_by("first_visit").first()
    stats_started_on = first_record.first_visit.date() if first_record else None

    return {
        "total_visitors": total_visitors,
        "visitors_today": visitors_today,
        "returning_visitors": returning_visitors,
    }
