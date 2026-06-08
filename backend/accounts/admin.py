from django.contrib import admin
from campus.admin import campus_admin_site
from .models import Profile, School, Department


@admin.register(Profile, site=campus_admin_site)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "university",
        "school",
        "department",
        "role",
        "matric_number",
        "level",
    )

    search_fields = (
        "user__username",
        "matric_number",
    )


@admin.register(School, site=campus_admin_site)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name","university",)
    search_fields = ("name",)


@admin.register(Department, site=campus_admin_site)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "school", )
    search_fields = ("name",)