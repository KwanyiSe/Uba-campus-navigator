"""B4 attendance UI view.

This view only renders the attendance UI. Attendance verification remains in B2/B3.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from academic.models import ClassSession


@login_required
def class_detail(request, session_id):
    session = get_object_or_404(
        ClassSession.objects.select_related("course", "building"),
        pk=session_id,
    )

    return render(
        request,
        "academic/class_detail.html",
        {"session": session},
    )
