from django.contrib.admin import AdminSite
from django.contrib import admin
from django.utils import timezone
from django.db import models

# Import models
from .models import Building, SiteVisit, DailyStats, University, CampusAdminUser

# Import default auth models
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.admin.sites import AlreadyRegistered

# ---------------------------
# Custom Admin Site
# ---------------------------
class CampusAdminSite(AdminSite):
    """Custom admin site for UBA campus management."""
    site_header = "UBA Campus Administration"

    def index(self, request, extra_context=None):
        """
        Overrides the default admin index page to include extra stats
        only visible to superusers.
        """
        if extra_context is None:
            extra_context = {}

        extra_context.update(admin_index(request))
        return super().index(request, extra_context)


# Instantiate custom admin site
campus_admin_site = CampusAdminSite(name="campus_admin")


# ---------------------------
# Register default auth models
# ---------------------------
try:
    campus_admin_site.register(User, UserAdmin)
except AlreadyRegistered:
    pass

try:
    campus_admin_site.register(Group, GroupAdmin)
except AlreadyRegistered:
    pass


# ---------------------------
# Helper: Admin Index Stats
# ---------------------------
def admin_index(request):
    """
    Returns visitor statistics.
    Superuser → sees all universities
    Campus admin → sees only their university
    """

    today = timezone.now().date()

    # super user global stats
    if request.user.is_superuser:
        total_visitors = DailyStats.objects.aggregate(
            total=models.Sum("visitors")
        )["total"] or 0

        visitors_today = DailyStats.objects.filter(date=today).aggregate(
            total=models.Sum("visitors")
        )["total"] or 0

        return {
            "total_visitors": total_visitors,
            "visitors_today": visitors_today,
        }

    # campus admin only their university
    if hasattr(request.user, "campus_admin"):
        university = request.user.campus_admin.university

        total_visitors = DailyStats.objects.filter(
            building__university=university
        ).aggregate(
            total=models.Sum("visitors")
        )["total"] or 0

        visitors_today = DailyStats.objects.filter(
            date=today,
            building__university=university
        ).aggregate(
            total=models.Sum("visitors")
        )["total"] or 0

        return {
            "total_visitors": total_visitors,
            "visitors_today": visitors_today,
        }

    return {}

# ---------------------------
# Admin for University
# ---------------------------
@admin.register(University, site=campus_admin_site)
class UniversityAdmin(admin.ModelAdmin):
    """Superusers can manage all universities."""
    list_display = ("name", "short_name", "country")
    search_fields = ("name", "short_name")


# ---------------------------
# Admin for Building
# ---------------------------
@admin.register(Building, site=campus_admin_site)
class BuildingAdmin(admin.ModelAdmin):
    """Filters buildings per university for non-superusers."""
    list_display = ("name", "category", "university")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter buildings by the user's university
        return qs.filter(university=request.user.campus_admin.university)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            # Automatically assign university to the building
            obj.university = request.user.campus_admin.university
        super().save_model(request, obj, form, change)


# ---------------------------
# Admin for DailyStats
# ---------------------------
@admin.register(DailyStats, site=campus_admin_site)
class DailyStatsAdmin(admin.ModelAdmin):
    """Filter stats per university via building."""
    list_display = ("date", "visitors")
    ordering = ("-date",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter by user's university through building
        return qs.filter(building__university=request.user.campus_admin.university)


# ---------------------------
# Admin for SiteVisit
# ---------------------------
@admin.register(SiteVisit, site=campus_admin_site)
class SiteVisitAdmin(admin.ModelAdmin):
    """Filter site visits per university via building."""
    list_display = ("session_key", "first_visit", "last_visit")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Filter by user's university through building
        return qs.filter(building__university=request.user.campus_admin.university)
