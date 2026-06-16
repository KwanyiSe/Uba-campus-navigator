from django.contrib import admin
from campus.admin import campus_admin_site
from .models import Feedback


@admin.register(Feedback, site=campus_admin_site)
class FeedbackAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "subject",
        "status",
        "user",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "subject",
        "message",
        "name",
        "email",
    )

    ordering = ("-created_at",)