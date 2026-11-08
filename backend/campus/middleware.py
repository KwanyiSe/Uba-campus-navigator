from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import DailyStats, DailyVisit, SiteVisit, University


class SiteVisitMiddleware:
    """Count unique browser sessions once per university per local calendar day.

    A database uniqueness constraint, rather than a cache-only flag, prevents
    concurrent requests and multiple app workers from counting the same session
    twice. The short cache only throttles SiteVisit.last_visit writes.
    """

    EXCLUDED_PREFIXES = ("/admin/", "/static/", "/media/", "/health/")
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
                if cache.add(touch_key, "1", timeout=self.VISIT_TOUCH_SECONDS):
                    try:
                        self._record_visit(request, university.pk, session_key, today)
                    except Exception:
                        cache.delete(touch_key)
                        raise
        except Exception:
            # Analytics are non-critical: never prevent the requested page loading.
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
                university = University.objects.filter(
                    short_name__iexact=prefix, active=True
                ).only("id").first()
            if university is None:
                university = University.objects.filter(active=True).only("id").order_by("id").first()
            university_id = university.pk if university else 0
            cache.set(cache_key, university_id, cls.UNIVERSITY_CACHE_SECONDS)
        return University(pk=university_id) if university_id else None

    @staticmethod
    def _record_visit(request, university_id, session_key, today):
        now = timezone.now()
        with transaction.atomic():
            visit, created = SiteVisit.objects.get_or_create(
                session_key=session_key,
                defaults={"university_id": university_id},
            )
            if not created:
                SiteVisit.objects.filter(pk=visit.pk).update(
                    last_visit=now, university_id=university_id
                )

            # This unique insert is the source of truth for daily unique visitors.
            daily_visit, counted_today = DailyVisit.objects.get_or_create(
                session_key=session_key,
                university_id=university_id,
                date=today,
            )
            if counted_today:
                stats, _ = DailyStats.objects.get_or_create(
                    university_id=university_id, date=today
                )
                DailyStats.objects.filter(pk=stats.pk).update(visitors=F("visitors") + 1)
