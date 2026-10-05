from datetime import timedelta
from django.contrib.auth.models import User
from django.test import override_settings
from django.urls import include, path
from django.utils import timezone
from rest_framework.test import APITestCase
from accounts.models import Profile
from academic.models import AttendanceRecord, ClassSession, Course, Enrollment
from campus.models import Building, BuildingGeofence, University

urlpatterns = [path("api/", include("academic.urls"))]

@override_settings(ROOT_URLCONF=__name__)
class AttendanceAPITests(APITestCase):
    def setUp(self):
        now = timezone.localtime(timezone.now()).replace(second=0, microsecond=0)
        self.start = now - timedelta(minutes=10)
        self.end = now + timedelta(hours=1)
        self.university = University.objects.create(name="Test University", short_name="TU", country="Cameroon")
        self.building = Building.objects.create(name="Engineering Block", latitude=5.9635, longitude=10.1595, university=self.university)
        BuildingGeofence.objects.create(building=self.building, center_lat=5.9635, center_lng=10.1595, radius=100, polygon=[{"lat":5.9630,"lng":10.1590},{"lat":5.9640,"lng":10.1590},{"lat":5.9640,"lng":10.1600},{"lat":5.9630,"lng":10.1600}], is_active=True)
        self.user = User.objects.create_user(username="student1", password="testpass123")
        self.profile = Profile.objects.create(user=self.user)
        self.course = Course.objects.create(university=self.university, code="CSE101", name="Computer Science 101")
        Enrollment.objects.create(student=self.profile, course=self.course, active=True)
        self.session = ClassSession.objects.create(course=self.course, level=100, building=self.building, day_of_week=self.start.weekday(), start_time=self.start.time(), end_time=self.end.time(), session_date=self.start.date(), status="active", started_at=self.start, active=True, created_by=self.user)
        self.client.force_authenticate(user=self.user)
        self.payload = {"session_id": self.session.id, "latitude":5.9635, "longitude":10.1595, "accuracy":10}

    def test_successful_attendance_mark(self):
        r=self.client.post("/api/attendance/mark/", self.payload, format="json")
        self.assertEqual(r.status_code,201); self.assertTrue(r.data["success"]); self.assertEqual(r.data["window"],"initial")

    def test_unenrolled_student_rejected(self):
        Enrollment.objects.filter(student=self.profile, course=self.course).update(active=False)
        r=self.client.post("/api/attendance/mark/", self.payload, format="json")
        self.assertEqual(r.status_code,403)

    def test_inactive_session_rejected(self):
        self.session.status="completed"; self.session.active=False; self.session.save(update_fields=["status","active"])
        r=self.client.post("/api/attendance/mark/", self.payload, format="json")
        self.assertEqual(r.status_code,400)

    def test_outside_geofence_rejected(self):
        r=self.client.post("/api/attendance/mark/", {**self.payload,"latitude":5.9700,"longitude":10.1700}, format="json")
        self.assertEqual(r.status_code,403)

    def test_location_verified_spoof_rejected(self):
        r=self.client.post("/api/attendance/mark/", {**self.payload,"location_verified":True}, format="json")
        self.assertEqual(r.status_code,400); self.assertIn("location_verified", r.data["details"])

    def test_student_id_rejected(self):
        r=self.client.post("/api/attendance/mark/", {**self.payload,"student_id":999999}, format="json")
        self.assertEqual(r.status_code,400); self.assertIn("student_id", r.data["details"])

    def test_duplicate_rejected(self):
        AttendanceRecord.objects.create(session=self.session, student=self.profile, status="present", verification_method="automatic")
        r=self.client.post("/api/attendance/mark/", self.payload, format="json")
        self.assertEqual(r.status_code,409)
