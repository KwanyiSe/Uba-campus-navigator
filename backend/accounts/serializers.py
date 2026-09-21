from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    Profile,
    School,
    Department
)


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    university = serializers.IntegerField()
    school = serializers.IntegerField(required=False)
    department = serializers.IntegerField(required=False)

    level = serializers.IntegerField(required=False)

    matric_number = serializers.CharField(
        required=False,
        allow_blank=True
    )

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "password",

            "university",
            "school",
            "department",

            "level",
            "matric_number"
        ]
        
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already exists"
            )

        return value

    def validate_level(self, value):

        if value < 100:
            raise serializers.ValidationError(
                "Level must be at least 100"
            ) # like 100 200 ect not 50 +- 

        return value
    

    def create(self, validated_data):

        university_id = validated_data.pop("university")

        school_id = validated_data.pop("school", None)

        department_id = validated_data.pop("department", None)

        level = validated_data.pop("level", None)

        matric_number = validated_data.pop(
            "matric_number",
            None
        )

        user = User.objects.create_user(
            **validated_data
        )

        school = None
        department = None

        if school_id:
            school = School.objects.get(
                id=school_id
            )

        if department_id:
            department = Department.objects.get(
                id=department_id
            )

        Profile.objects.create(
            user=user,
            university_id=university_id,

            school=school,
            department=department,

            level=level,

            matric_number=matric_number or None,

            role="student"
        )

        return user
    
    
    def validate(self, attrs):
        university_id = attrs.get("university")
        school_id = attrs.get("school")
        department_id = attrs.get("department")

        if school_id:

            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                raise serializers.ValidationError(
                    "School not found"
                )

            if school.university_id != university_id:
                raise serializers.ValidationError(
                    "School does not belong to selected university"
                )

        if department_id:

            try:
                department = Department.objects.get(
                    id=department_id
                )
            except Department.DoesNotExist:
                raise serializers.ValidationError(
                    "Department not found"
                )

            if school_id and department.school_id != school_id:
                raise serializers.ValidationError(
                    "Department does not belong to selected school"
                )

        return attrs
    
    
class ProfileUpdateSerializer(serializers.ModelSerializer):
    """allow students to update their school dpt level and matricle."""
    class Meta:
        model = Profile

        fields = [
            "school",
            "department",
            "level",
            "matric_number",
        ]

    def validate(self, attrs):

        school = attrs.get(
            "school",
            self.instance.school
        )

        department = attrs.get(
            "department",
            self.instance.department
        )

        if school and department:

            if department.school_id != school.id:

                raise serializers.ValidationError(
                    "Department does not belong to selected school"
                )

        return attrs