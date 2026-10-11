from campus.admin import campus_admin_site
from django.contrib import admin
from .models import Course,Timetable,ClassCoordinatorAssignment,ClassSession,Enrollment,AttendanceRecord,CampusActivity,NewsPost,NewsAttachment,AcademicYear,Semester,FormB,FormBCourse
@admin.register(Course, site=campus_admin_site)
class CourseAdmin(admin.ModelAdmin): list_display=("code","name","university","department","lecturer","active")
@admin.register(Timetable, site=campus_admin_site)
class TimetableAdmin(admin.ModelAdmin): list_display=("title","option","level","uploaded_by","uploaded_at","active")
@admin.register(ClassCoordinatorAssignment, site=campus_admin_site)
class CCAAdmin(admin.ModelAdmin): list_display=("coordinator","option","level","active")
@admin.register(ClassSession, site=campus_admin_site)
class SessionAdmin(admin.ModelAdmin): list_display=("course","option","level","session_date","start_time","end_time","status")
@admin.register(Enrollment, site=campus_admin_site)
class EnrollmentAdmin(admin.ModelAdmin): list_display=("student","course","active")
@admin.register(AttendanceRecord, site=campus_admin_site)
class AttendanceAdmin(admin.ModelAdmin): list_display=("student","session","status","verification_method","updated_at")
@admin.register(CampusActivity, site=campus_admin_site)
class ActivityAdmin(admin.ModelAdmin): list_display=("title","activity_type","university","active")
@admin.register(NewsPost, site=campus_admin_site)
class NewsPostAdmin(admin.ModelAdmin): list_display=("title","post_type","audience","university","author","created_at","active")
@admin.register(NewsAttachment, site=campus_admin_site)
class NewsAttachmentAdmin(admin.ModelAdmin): list_display=("post","original_name","uploaded_at")


@admin.register(AcademicYear, site=campus_admin_site)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display=("name","start_date","end_date","active")

@admin.register(Semester, site=campus_admin_site)
class SemesterAdmin(admin.ModelAdmin):
    list_display=("academic_year","name","start_date","end_date","active")
    list_filter=("name","active")

@admin.register(FormB, site=campus_admin_site)
class FormBAdmin(admin.ModelAdmin):
    list_display=("department","option","level","academic_year","semester","status","uploaded_at")
    list_filter=("status","academic_year","semester")
    search_fields=("department__name","option__name","title")

@admin.register(FormBCourse, site=campus_admin_site)
class FormBCourseAdmin(admin.ModelAdmin):
    list_display=("form_b","source_code","source_name","course","position")
#@kwanyi :)