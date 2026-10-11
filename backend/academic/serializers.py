from rest_framework import serializers
from .models import Course, ClassSession, Enrollment, AttendanceRecord, CampusActivity, Timetable, NewsPost, NewsAttachment, AcademicYear, Semester, FormB, FormBCourse


#Kwanyise@
class CourseSerializer(serializers.ModelSerializer):
    lecturer_name = serializers.SerializerMethodField()
    class Meta:
        model=Course
        fields=["id","university","code","name","description","department","lecturer","lecturer_name","active"]
    def get_lecturer_name(self,obj): return obj.lecturer.profile.display_name() if obj.lecturer and hasattr(obj.lecturer,"profile") else None

class ClassSessionSerializer(serializers.ModelSerializer):
    course_code=serializers.CharField(source="course.code",read_only=True)
    course_name=serializers.CharField(source="course.name",read_only=True)
    building_name=serializers.CharField(source="building.name",read_only=True,allow_null=True)
    option_name=serializers.CharField(source="option.name",read_only=True,allow_null=True)
    def validate(self, attrs):
        form_b=attrs.get("form_b")
        course=attrs.get("course")
        option=attrs.get("option")
        level=attrs.get("level")
        if form_b:
            if form_b.option_id != getattr(option, "id", None) or form_b.level != level:
                raise serializers.ValidationError("The Form B cohort does not match this class option and level.")
            if course and course.university_id != form_b.university_id:
                raise serializers.ValidationError("The course and Form B belong to different universities.")
            if not form_b.courses.filter(course=course).exists():
                raise serializers.ValidationError("The selected course is not present on this Form B.")
        return attrs

    class Meta:
        model=ClassSession
        fields=["id","course","course_code","course_name","form_b","option","option_name","level","building","building_name","room","day_of_week","start_time","end_time","session_date","status","started_at","ended_at","lecturer","coordinator","created_by","notes","active"]

class EnrollmentSerializer(serializers.ModelSerializer):
    course_code=serializers.CharField(source="course.code",read_only=True); course_name=serializers.CharField(source="course.name",read_only=True)
    class Meta: model=Enrollment; fields=["id","course","course_code","course_name","form_b","enrolled_at","active"]

class AttendanceSerializer(serializers.ModelSerializer):
    student_name=serializers.CharField(source="student.full_name",read_only=True)
    matric_number=serializers.CharField(source="student.matric_number",read_only=True)
    class Meta: model=AttendanceRecord; fields=["id","session","student","student_name","matric_number","status","verification_method","latitude","longitude","accuracy","verified_at","updated_at"]

class CampusActivitySerializer(serializers.ModelSerializer):
    building_name=serializers.CharField(source="building.name",read_only=True,allow_null=True)
    class Meta: model=CampusActivity; fields=["id","title","description","activity_type","start_at","end_at","building","building_name","active","university"]

class TimetableSerializer(serializers.ModelSerializer):
    class Meta: model=Timetable; fields=["id","university","school","department","option","level","title","file","uploaded_by","uploaded_at","active"]; read_only_fields=["uploaded_by","uploaded_at"]

class NewsAttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = NewsAttachment
        fields = [
            "id",
            "file",
            "file_url",
            "original_name",
            "uploaded_at",
        ]

    def get_file_url(self, obj):
        if not obj.file:
            return None

        try:
            url = obj.file.url
        except (ValueError, AttributeError):
            return None

        request = self.context.get("request")
        if request and url and not url.startswith(("http://", "https://")):
            return request.build_absolute_uri(url)

        return url


class NewsPostSerializer(serializers.ModelSerializer):

    attachments = NewsAttachmentSerializer(many=True, read_only=True)
    author_name = serializers.SerializerMethodField()
    author_avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = NewsPost
        fields = [
            "id",
            "university",
            "author",
            "author_name",
            "author_avatar_url",
            "post_type",
            "title",
            "body",
            "audience",
            "school",
            "department",
            "option",
            "level",
            "attachments",
            "created_at",
            "updated_at",
            "active",
        ]

        read_only_fields = [
            "id",
            "author_name",
            "created_at",
            "updated_at",
            "active",
        ]
        
    def get_author_name(self, obj):
        if obj.author:
            return obj.author.display_name()
        return None

    def get_author_avatar_url(self, obj):
        if not obj.author or not obj.author.profile_picture:
            return None
        try:
            return obj.author.profile_picture.url
        except (ValueError, AttributeError):
            return None


class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model=AcademicYear
        fields=["id","name","start_date","end_date","active"]

class SemesterSerializer(serializers.ModelSerializer):
    academic_year_name=serializers.CharField(source="academic_year.name",read_only=True)
    class Meta:
        model=Semester
        fields=["id","academic_year","academic_year_name","name","start_date","end_date","active"]

class FormBCourseSerializer(serializers.ModelSerializer):
    course_code=serializers.CharField(source="course.code",read_only=True)
    course_name=serializers.CharField(source="course.name",read_only=True)
    class Meta:
        model=FormBCourse
        fields=["id","course","course_code","course_name","source_code","source_name","position"]

class FormBSerializer(serializers.ModelSerializer):
    courses=FormBCourseSerializer(many=True,read_only=True)
    academic_year_name=serializers.CharField(source="academic_year.name",read_only=True)
    semester_name=serializers.CharField(source="semester.get_name_display",read_only=True)
    class Meta:
        model=FormB
        fields=["id","university","academic_year","academic_year_name","semester","semester_name","department","option","level","title","file","uploaded_by","uploaded_at","status","parsed_at","courses"]
        read_only_fields=["uploaded_by","uploaded_at","status","parsed_at"]
