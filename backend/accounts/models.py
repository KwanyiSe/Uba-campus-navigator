from django.db import models
from django.contrib.auth.models import User
from campus.models import University


class School(models.Model):
    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name="schools"
    )

    name = models.CharField(max_length=150)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.university.short_name})"


class Department(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="departments"
    )

    name = models.CharField(max_length=150)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Profile(models.Model):

    ROLE_CHOICES = (
        ('student', 'Student'),
        ('lecturer', 'Lecturer'),
        ('cc', 'Class Coordinator'),
        ('admin', 'Admin'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE
    )

    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profiles"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profiles"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student'
    )

    matric_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )

    admission_year = models.IntegerField(
        null=True,
        blank=True
    )

    level = models.IntegerField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.university.short_name}"