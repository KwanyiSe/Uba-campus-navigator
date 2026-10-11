from django.db import models
from django.contrib.auth.models import User
from campus.models import University
from unimap_project.storage import ProfileMediaStorage


class School(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name="schools")
    name = models.CharField(max_length=150)
    logo = models.ImageField(upload_to="schools/logos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.university.short_name})"


class Department(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=150)
    logo = models.ImageField(upload_to="departments/logos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Option(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="options")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=40, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["department", "name"], name="unique_option_per_department")
        ]

    def __str__(self):
        return f"{self.name} ({self.department.name})"


class Profile(models.Model):
    ROLE_CHOICES = (
        ("student", "Student"),
        ("lecturer", "Lecturer"),
        ("cc", "Class Coordinator"),
        ("school_admin", "School Admin"),
        ("admin", "University Admin"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=180, blank=True)
    
    
    profile_picture = models.ImageField(
    storage=ProfileMediaStorage(),
    upload_to="profiles/",
    blank=True,
    null=True,)
        
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name="profiles")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="profiles")
    option = models.ForeignKey(Option, on_delete=models.SET_NULL, null=True, blank=True, related_name="profiles")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    matric_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    admission_year = models.IntegerField(null=True, blank=True)
    level = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def display_name(self):
        return self.full_name.strip() or self.user.get_full_name().strip() or self.user.username

    def initials(self):
        parts = self.display_name().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return self.display_name()[:2].upper()

    def __str__(self):
        return f"{self.display_name()} - {self.university.short_name}"


class Notification(models.Model):
    TYPE_CHOICES = (
        ("general", "General"),
        ("class", "Class"),
        ("attendance", "Attendance"),
        ("form_b", "Form B"),
        ("news", "News"),
        ("staff", "Staff"),
    )
    recipient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="notifications")
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="general")
    title = models.CharField(max_length=180)
    body = models.TextField(blank=True)
    link = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_read(self):
        return self.read_at is not None

    def __str__(self):
        return f"{self.recipient.display_name()} — {self.title}"
