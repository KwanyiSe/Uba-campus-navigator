from datetime import datetime, timedelta
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import Profile
from academic.models import AttendanceRecord, ClassSession, Enrollment
from academic.serializers import AttendanceMarkSerializer
from academic.services.geofence_service import verify_location

def attendance_is_open(session, now=None):
    """Attendance is available continuously from session start to finish"""

    if now is None:
        now = timezone.now()
        if not session.started_at or not session.ended_at:
            return False

            return session.started_at <= now <= session.ended_at

class MarkAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = AttendanceMarkSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "error": "Invalid attendance data.", "details": serializer.errors}, status=400)
        session_id = serializer.validated_data["session_id"]
        try:
            session = ClassSession.objects.select_related("course", "building").get(pk=session_id)
        except ClassSession.DoesNotExist:
            return Response({"success": False, "error": "Class session not found."}, status=404)
        if not session.active or session.status != "active":
            return Response({"success": False, "error": "Attendance is only available for an active session."}, status=400)
        if session.building is None:
            return Response({"success": False, "error": "This session has no attendance building configured."}, status=400)
        if not attendance_is_open(session):
            return Response(
                {"detail": "Attendance is not currently open."},

                status=400)
        try:
            student = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response({"success": False, "error": "Student profile not found."}, status=403)
        if not Enrollment.objects.filter(student=student, course=session.course, active=True).exists():
            return Response({"success": False, "error": "Student is not enrolled in this course."}, status=403)
        if AttendanceRecord.objects.filter(session=session, student=student).exists():
            return Response({"success": False, "error": "Attendance has already been marked for this session."}, status=409)
        result = verify_location(session.building, serializer.validated_data["latitude"], serializer.validated_data["longitude"], serializer.validated_data["accuracy"])
        if not result["verified"]:
            return Response({"success": False, "error": result["reason"]}, status=403)
        try:
            attendance = AttendanceRecord.objects.create(session=session, student=student, status="present", verification_method="automatic")
        except IntegrityError:
            return Response({"success": False, "error": "Attendance has already been marked for this session."}, status=409)
        return Response({"success": True, "message": "Attendance marked successfully.", "attendance_id": attendance.id, "session_id": session.id, "window": window, "status": attendance.status, "verification_method": attendance.verification_method}, status=201)
