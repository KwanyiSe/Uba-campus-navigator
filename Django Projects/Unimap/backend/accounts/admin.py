from django.contrib import admin
from campus.admin import campus_admin_site
from .models import Profile, School, Department, Option

@admin.register(Profile, site=campus_admin_site)
class ProfileAdmin(admin.ModelAdmin):
    list_display=("user","full_name","university","school","department","option","role","matric_number","level")
    search_fields=("user__username","user__email","full_name","matric_number")

@admin.register(School, site=campus_admin_site)
class SchoolAdmin(admin.ModelAdmin):
    list_display=("name","university","logo");search_fields=("name",)

@admin.register(Department, site=campus_admin_site)
class DepartmentAdmin(admin.ModelAdmin):
    list_display=("name","school","logo");search_fields=("name",)

@admin.register(Option, site=campus_admin_site)
class OptionAdmin(admin.ModelAdmin):
    list_display=("name","code","department","active");list_filter=("active",)
    search_fields=("name","code","department__name")
