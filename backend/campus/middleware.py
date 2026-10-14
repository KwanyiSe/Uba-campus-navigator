from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import SiteVisit, DailyStats, University


class SiteVisitMiddleware:
    """Count at most one visit per browser session, university and local day.

    Static assets, admin pages and unsafe methods are excluded so CSS/images/API
    mutations do not inflate visitor counts. A session is a practical anonymous
    visitor approximation; it is not a cross-device person count.
    """

    EXCLUDED_PREFIXES = ("/admin/", "/static/", "/media/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in ("GET", "HEAD") or request.path.startswith(self.EXCLUDED_PREFIXES):
            return self.get_response(request)

        try:
            university = self._get_university(request.path)
            if university is None:
                return self.get_response(request)

            if not request.session.session_key:
                request.session.create()
            session_key = request.session.session_key
            today = timezone.localdate()

            with transaction.atomic():
                visit, created = SiteVisit.objects.get_or_create(
                    session_key=session_key,
                    defaults={"university": university},
                )
                # Refresh last_visit and associate the session with the university
                # it is actively visiting, without creating duplicate session rows.
                fields = []
                if visit.university_id != university.id:
                    visit.university = university
                    fields.append("university")
                visit.last_visit = timezone.now()
                fields.append("last_visit")
                visit.save(update_fields=fields)

                counted_key = f"counted_date_{university.id}"
                if request.session.get(counted_key) != today.isoformat():
                    stats, _ = DailyStats.objects.get_or_create(
                        university=university,
                        date=today,
                    )
                    # Use an F expression to avoid lost increments under concurrent requests.
                    from django.db.models import F
                    DailyStats.objects.filter(pk=stats.pk).update(visitors=F("visitors") + 1)
                    request.session[counted_key] = today.isoformat()
        except (IntegrityError, ValueError, TypeError):
            # Analytics must never make the actual page unavailable.
            pass

        return self.get_response(request)

    @staticmethod
    def _get_university(path):
        parts = [part for part in path.strip("/").split("/") if part]
        if parts:
            university = University.objects.filter(short_name__iexact=parts[0], active=True).first()
            if university:
                return university
        return University.objects.filter(active=True).order_by("id").first()
