from django.urls import path
from .views import *
from academic.views import MarkAttendanceView
from django.views.generic import TemplateView

urlpatterns=[
 path("courses/",CourseListView.as_view(),name="course-list"),
 path("sessions/",ClassSessionListView.as_view(),name="class-session-list"),
 path("classes/",MyClassesView.as_view(),name="my-classes-api"),
 path("schedule/",MyScheduleView.as_view(),name="my-schedule-api"),
 path("halls/",HallAvailabilityView.as_view(),name="hall-availability-api"),
 path("attendance/",MyAttendanceView.as_view(),name="my-attendance-api"),
 path("activities/",CampusActivityListView.as_view(),name="campus-activity-list"),
 path("overview/",CampusOverviewView.as_view(),name="campus-overview"),
 path("timetables/",TimetableView.as_view(),name="timetables"),
 path("staff/",StaffDirectoryView.as_view(),name="staff-directory"),
 path("staff/assign/",StaffAssignmentView.as_view(),name="staff-assign"),
 path("class-sessions/create/",ClassSessionCreateView.as_view(),name="class-session-create"),
 path("class-sessions/<int:pk>/action/",ClassSessionActionView.as_view(),name="class-session-action"),
 path("class-sessions/<int:pk>/attendance/",AttendanceListView.as_view(),name="class-session-attendance"),
 path("class-sessions/<int:pk>/attendance/download/",AttendanceDownloadView.as_view(),name="attendance-download"),
 path("class-sessions/<int:pk>/mark-attendance/",MarkAttendanceView.as_view(),name="mark-attendance"),
 path("news/",NewsFeedView.as_view(),name="news-feed"),
 path("news/create/",NewsCreateView.as_view(),name="news-create"),
 path("attendance/mark/", MarkAttendanceView.as_view(), name="mark-attendance"),
]
