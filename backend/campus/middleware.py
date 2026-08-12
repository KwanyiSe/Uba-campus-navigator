from django.db import IntegrityError
from django.utils import timezone

from .models import (
    SiteVisit,
    DailyStats,
    University)


class SiteVisitMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Ignore admin and static files
        if (
            request.path.startswith("/admin/")
            or request.path.startswith("/static/")
            or request.path.startswith("/media/")
        ):
            return self.get_response(request)

        # Ensure session exists
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

  
        try:

            university = None

            path_parts = request.path.strip("/").split("/")

            if path_parts and path_parts[0]:
                university = University.objects.filter(
                    short_name__iexact=path_parts[0]
                ).first()

            if university:
                SiteVisit.objects.get_or_create(
                    session_key=session_key,
                    defaults={
                        "university": university
                    }
                )

        except IntegrityError:
            pass

        # -------------------------
        # Determine University
        # -------------------------

        university = None

        path_parts = [
            p for p in request.path.strip("/").split("/")
            if p
        ]

        if path_parts:
            short_name = path_parts[0]

            university = University.objects.filter(
                short_name__iexact=short_name,
                active=True
            ).first()

        if not university:
            university = University.objects.filter(
                active=True
            ).first()

        # No university configured
        if not university:
            return self.get_response(request)

        # -------------------------
        # Daily Statistics
        # -------------------------

        today = timezone.now().date()

        stats, _ = DailyStats.objects.get_or_create(
            university=university,
            date=today,
        )

        last_counted = request.session.get(
            f"counted_date_{university.id}"
        )

        if last_counted != str(today):
            stats.visitors += 1
            stats.save()

            request.session[
                f"counted_date_{university.id}"
            ] = str(today)

        return self.get_response(request)