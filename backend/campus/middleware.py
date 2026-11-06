from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from .models import SiteVisit, DailyStats, University


class SiteVisitMiddleware:
    """Record lightweight visit analytics without slowing every page request.

    Static/admin/media paths and unsafe methods are ignored. University resolution is
    cached for ten minutes, and a session's SiteVisit row is touched at most once per
    ten minutes. DailyStats still increments at most once per session/university/day.
    """

    EXCLUDED_PREFIXES = ("/admin/", "/static/", "/media/")
    UNIVERSITY_CACHE_SECONDS = 600
    VISIT_TOUCH_SECONDS = 600

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in ("GET", "HEAD") or request.path.startswith(self.EXCLUDED_PREFIXES):
            return self.get_response(request)

        try:
            university = self._get_university(request.path)
            if university is not None:
                if not request.session.session_key:
                    request.session.create()

                session_key = request.session.session_key
                today = timezone.localdate()
                touch_key = f"unimap:sitevisit-touch:{session_key}:{university.pk}"

                # A cache hit avoids all analytics database queries on ordinary page views.
                if cache.add(touch_key, "1", timeout=self.VISIT_TOUCH_SECONDS):
                    try:
                        self._record_visit(request, university, session_key, today)
                    except Exception:
                        # Analytics must never prevent the requested page from loading.
                        cache.delete(touch_key)
        except Exception:
            # Fail open: analytics is non-critical and must not affect navigation.
            pass

        return self.get_response(request)

    @classmethod
    def _get_university(cls, path):
        parts = [part for part in path.strip("/").split("/") if part]
        prefix = parts[0].lower() if parts else "__default__"
        cache_key = f"unimap:visit-university:{prefix}"
        university_id = cache.get(cache_key)
        if university_id is None:
            university = None
            if prefix != "__default__":
                university = University.objects.filter(short_name__iexact=prefix, active=True).only("id").first()
            if university is None:
                university = University.objects.filter(active=True).only("id").order_by("id").first()
            university_id = university.pk if university else 0
            cache.set(cache_key, university_id, cls.UNIVERSITY_CACHE_SECONDS)
        if not university_id:
            return None
        # Middleware only needs the foreign-key id; avoid fetching all university columns.
        return University(pk=university_id)

    @staticmethod
    def _record_visit(request, university, session_key, today):
        now = timezone.now()
        with transaction.atomic():
            visit, created = SiteVisit.objects.get_or_create(
                session_key=session_key,
                defaults={"university_id": university.pk},
            )
            if not created:
                updates = {"last_visit": now}
                if visit.university_id != university.pk:
                    updates["university_id"] = university.pk
                SiteVisit.objects.filter(pk=visit.pk).update(**updates)

            counted_key = f"counted_date_{university.pk}"
            if request.session.get(counted_key) != today.isoformat():
                stats, _ = DailyStats.objects.get_or_create(
                    university_id=university.pk,
                    date=today,
                )
                DailyStats.objects.filter(pk=stats.pk).update(visitors=F("visitors") + 1)
                request.session[counted_key] = today.isoformat()
