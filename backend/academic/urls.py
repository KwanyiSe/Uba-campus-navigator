from django.urls import path
from .views import *



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
 path("cc/workspace/",CCWorkspaceView.as_view(),name="cc-workspace"),
 path("staff/",StaffDirectoryView.as_view(),name="staff-directory"),
 #@kwanyi :)
 path("staff/assign/",StaffAssignmentView.as_view(),name="staff-assign"),
 path("class-sessions/create/",ClassSessionCreateView.as_view(),name="class-session-create"),
 path("class-sessions/<int:pk>/action/",ClassSessionActionView.as_view(),name="class-session-action"),
 path("class-sessions/<int:pk>/attendance/",AttendanceListView.as_view(),name="class-session-attendance"),
 path("class-sessions/<int:pk>/attendance/download/",AttendanceDownloadView.as_view(),name="attendance-download"),
 path("class-sessions/<int:pk>/mark-attendance/",MarkAttendanceView.as_view(),name="mark-attendance"),
 path("academic-years/",AcademicYearListView.as_view(),name="academic-years"),
 path("semesters/",SemesterListView.as_view(),name="semesters"),
 path("form-b/",FormBListCreateView.as_view(),name="form-b-list-create"),
 path("form-b/<int:pk>/publish/",FormBPublishView.as_view(),name="form-b-publish"),
 path("notifications/",NotificationListView.as_view(),name="notifications-api"),
 path("news/",NewsFeedView.as_view(),name="news-feed"),
 path("news/create/",NewsCreateView.as_view(),name="news-create"),
]
