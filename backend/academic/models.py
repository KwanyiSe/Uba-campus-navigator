from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from accounts.models import Profile, Option
from campus.models import Building, University

#Kwanyise@
from unimap_project.storage import NewsMediaStorage
class Course(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="courses")
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    department = models.ForeignKey("accounts.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="courses")
    lecturer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="taught_courses")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]
        constraints = [models.UniqueConstraint(fields=["university", "code"], name="unique_course_code_per_university")]

    def __str__(self):
        return f"{self.code} — {self.name}"


class AcademicYear(models.Model):
    name = models.CharField(max_length=30, unique=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-name"]

    def __str__(self):
        return self.name


class Semester(models.Model):
    SEMESTER_CHOICES = (("semester_1", "Semester 1"), ("semester_2", "Semester 2"))
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="semesters")
    name = models.CharField(max_length=20, choices=SEMESTER_CHOICES)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["academic_year", "name"]
        constraints = [models.UniqueConstraint(fields=["academic_year", "name"], name="unique_semester_per_academic_year")]

    def __str__(self):
        return f"{self.academic_year} — {self.get_name_display()}"


class FormB(models.Model):
    STATUS_CHOICES = (("draft", "Draft"), ("published", "Published"), ("archived", "Archived"))
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="form_bs")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="form_bs")
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, related_name="form_bs")
    department = models.ForeignKey("accounts.Department", on_delete=models.PROTECT, related_name="form_bs")
    option = models.ForeignKey(Option, on_delete=models.PROTECT, related_name="form_bs")
    level = models.IntegerField()
    title = models.CharField(max_length=180, blank=True)
    file = models.FileField(upload_to="academic/form_b/")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="uploaded_form_bs")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="draft")
    parsed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]
        constraints = [models.UniqueConstraint(fields=["university", "academic_year", "semester", "department", "option", "level"], name="unique_form_b_cohort_semester")]

    def __str__(self):
        return f"{self.department.name} / {self.option.name} / L{self.level} / {self.semester}"


class FormBCourse(models.Model):
    form_b = models.ForeignKey(FormB, on_delete=models.CASCADE, related_name="courses")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="form_b_entries")
    source_code = models.CharField(max_length=30)
    source_name = models.CharField(max_length=150)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "source_code"]
        constraints = [models.UniqueConstraint(fields=["form_b", "course"], name="unique_course_per_form_b")]


class Timetable(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="timetables")
    school = models.ForeignKey("accounts.School", on_delete=models.CASCADE, related_name="timetables")
    department = models.ForeignKey("accounts.Department", on_delete=models.CASCADE, related_name="timetables")
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name="timetables")
    level = models.IntegerField()
    title = models.CharField(max_length=160)
    file = models.FileField(upload_to="academic/timetables/")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="uploaded_timetables")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-uploaded_at"]


class ClassCoordinatorAssignment(models.Model):
    coordinator = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="coordinator_assignments")
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name="coordinator_assignments")
    level = models.IntegerField()
    active = models.BooleanField(default=True)
    appointed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["option", "level"], name="unique_coordinator_per_option_level")]


class ClassSession(models.Model):
    DAY_CHOICES = tuple((i, name) for i, name in enumerate(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]))
    STATUS_CHOICES = (("scheduled","Scheduled"),("active","Active"),("completed","Completed"),("cancelled","Cancelled"))

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sessions")
    option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True, blank=True, related_name="class_sessions")
    level = models.IntegerField()
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True, related_name="class_sessions")
    room = models.CharField(max_length=80, blank=True)
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    session_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    lecturer = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="lecturer_sessions")
    coordinator = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="coordinator_sessions")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_class_sessions")
    notes = models.TextField(blank=True)
    form_b = models.ForeignKey("FormB", on_delete=models.SET_NULL, null=True, blank=True, related_name="class_sessions")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["session_date", "start_time"]

    def __str__(self):
        return f"{self.course.code} — {self.option.name} L{self.level}"


class Enrollment(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    form_b = models.ForeignKey("FormB", on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "course", "form_b"], name="unique_student_course_form_b_enrollment")]


class AttendanceRecord(models.Model):
    STATUS_CHOICES = (("present","Present"),("absent","Absent"))
    VERIFICATION_CHOICES = (("automatic","Automatic"),("manual","Manual"),("legacy","Legacy"))
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name="attendance")
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="absent")
    verification_method = models.CharField(max_length=20, choices=VERIFICATION_CHOICES, default="automatic")
    updated_at = models.DateTimeField(auto_now=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["session", "student"], name="unique_attendance_per_session_student")]


class CampusActivity(models.Model):
    ACTIVITY_TYPES = (("event","Event"),("group","Study Group"),("notice","Notice"))
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="activities")
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True, related_name="activities")
    title = models.CharField(max_length=160)
    description = models.CharField(max_length=255, blank=True)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, default="event")
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)


class NewsPost(models.Model):
    TYPE_CHOICES = (("study_group","Study Group"),("campus_news","Campus News"))
    AUDIENCE_CHOICES = (("university","Whole University"),("school","School"),("department","Department"),("option","Option"),("level","Level"))
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="news_posts")
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="news_posts")
    post_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=180)
    body = models.TextField()
    audience = models.CharField(max_length=20, choices=AUDIENCE_CHOICES, default="university")
    school = models.ForeignKey("accounts.School", on_delete=models.CASCADE, null=True, blank=True, related_name="news_posts")
    department = models.ForeignKey("accounts.Department", on_delete=models.CASCADE, null=True, blank=True, related_name="news_posts")
    option = models.ForeignKey(Option, on_delete=models.CASCADE, null=True, blank=True, related_name="news_posts")
    level = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]


class NewsAttachment(models.Model):
    post = models.ForeignKey(NewsPost, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(

        storage=NewsMediaStorage(),

        upload_to="news/",

    )
    original_name = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
