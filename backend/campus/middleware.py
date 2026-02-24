
from django.db import IntegrityError
from django.utils import timezone
from .models import SiteVisit, DailyStats

class SiteVisitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ignore admin & static files
        if request.path.startswith("/admin/") or request.path.startswith("/static/"):
            return self.get_response(request)

        # Ensure session exists
        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

        try:
            SiteVisit.objects.get_or_create(session_key=session_key)
        except IntegrityError:
            pass

        # AGGREGATION LOGIC
        today = timezone.now().date()

        # Create today's stats row if it doesn't exist
        stats, _ = DailyStats.objects.get_or_create(date=today)

        # Count this visitor only once per day
        if not request.session.get("counted_today"):
            stats.visitors += 1
            stats.save()
            request.session["counted_today"] = True

        return self.get_response(request)

