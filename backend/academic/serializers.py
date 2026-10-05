from rest_framework import serializers
from .models import Course, ClassSession, Enrollment, AttendanceRecord, CampusActivity, Timetable, NewsPost, NewsAttachment
from rest_framework import serializers


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
    class Meta:
        model=ClassSession
        fields=["id","course","course_code","course_name","option","option_name","level","building","building_name","room","day_of_week","start_time","end_time","session_date","status","started_at","ended_at","lecturer","coordinator","created_by","notes","active"]

class EnrollmentSerializer(serializers.ModelSerializer):
    course_code=serializers.CharField(source="course.code",read_only=True); course_name=serializers.CharField(source="course.name",read_only=True)
    class Meta: model=Enrollment; fields=["id","course","course_code","course_name","enrolled_at","active"]

class AttendanceSerializer(serializers.ModelSerializer):
    student_name=serializers.CharField(source="student.full_name",read_only=True)
    matric_number=serializers.CharField(source="student.matric_number",read_only=True)
    class Meta: model=AttendanceRecord; fields=["id","session","student","student_name","matric_number","status","verification_method","updated_at"]

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

class AttendanceMarkSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(min_value=1)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    accuracy = serializers.FloatField()

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

    def validate_latitude(self, value):
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value

    def validate_accuracy(self, value):
        if value < 0:
            raise serializers.ValidationError("GPS accuracy cannot be negative.")
        return value

    def validate(self, attrs):
        forbidden = {}
        if "student_id" in self.initial_data:
            forbidden["student_id"] = "This field is not accepted."
        if "location_verified" in self.initial_data:
            forbidden["location_verified"] = "This field is not accepted."
        if forbidden:
            raise serializers.ValidationError(forbidden)
        return attrs
