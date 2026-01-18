from django.db import IntegrityError
from .models import SiteVisit

class SiteVisitMiddleware:
    """
    Tracks unique visitors using Django sessions.

    - Ensures a session exists
    - Creates ONE SiteVisit per session
    - Handles race conditions safely
    """

    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):
        # ignore admin & static files, provent admin refresh counting
        if request.path.startswith("/admin/") or request.path.startswith("/static/"):
            return self.get_response(request)

        if not request.session.session_key:
            request.session.create()

        session_key = request.session.session_key

        try:
            SiteVisit.objects.get_or_create(session_key=session_key)
        except IntegrityError:
            pass

        return self.get_response(request)

