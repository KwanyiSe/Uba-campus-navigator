import re
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from campus.models import University
from .models import Profile, School, Department, Option


class RegisterSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(max_length=180)
    password = serializers.CharField(write_only=True, min_length=6)
    university = serializers.PrimaryKeyRelatedField(queryset=University.objects.filter(active=True))
    school = serializers.PrimaryKeyRelatedField(queryset=School.objects.all(), required=False, allow_null=True)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), required=False, allow_null=True)
    option = serializers.PrimaryKeyRelatedField(queryset=Option.objects.filter(active=True), required=False, allow_null=True)
    level = serializers.IntegerField(required=False, allow_null=True)
    matric_number = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ["full_name","email","password","university","school","department","option","level","matric_number","profile_picture"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate_level(self, value):
        if value is not None and value < 100:
            raise serializers.ValidationError("Level must be at least 100.")
        return value

    def validate(self, attrs):
        university, school = attrs.get("university"), attrs.get("school")
        department, option = attrs.get("department"), attrs.get("option")
        if school and school.university_id != university.id:
            raise serializers.ValidationError({"school":"School does not belong to selected university."})
        if department and (not school or department.school_id != school.id):
            raise serializers.ValidationError({"department":"Department does not belong to selected school."})
        if option and (not department or option.department_id != department.id):
            raise serializers.ValidationError({"option":"Option does not belong to selected department."})
        return attrs
        
    @transaction.atomic
    def create(self, validated_data):
        full_name = validated_data.pop("full_name").strip()

        university = validated_data.pop("university")
        school = validated_data.pop("school", None)
        department = validated_data.pop("department", None)
        option = validated_data.pop("option", None)
        level = validated_data.pop("level", None)
        matric = validated_data.pop("matric_number", None) or None
        picture = validated_data.pop("profile_picture", None)

        parts = full_name.split()
        first = parts[0]
        last = " ".join(parts[1:]) if len(parts) > 1 else ""

        base = re.sub(r"[^a-z0-9]+", "", full_name.lower()) or "user"

        username = base
        n = 1

        while User.objects.filter(username=username).exists():
            n += 1
            username = f"{base}{n}"

        user = User.objects.create_user(
            username=username,
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            first_name=first,
            last_name=last,
        )

        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults={
                "full_name": full_name,
                "profile_picture": picture,
                "university": university,
                "school": school,
                "department": department,
                "option": option,
                "level": level,
                "matric_number": matric,
                "role": "student",
            },)

        if not created:
            profile.full_name = full_name
            profile.university = university
            profile.school = school
            profile.department = department
            profile.option = option
            profile.level = level
            profile.matric_number = matric
            profile.role = "student"

            if picture:
                profile.profile_picture = picture

            profile.save()

        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["full_name","profile_picture","school","department","option","level","matric_number"]

    def validate(self, attrs):
        p = self.instance
        school = attrs.get("school", p.school); department = attrs.get("department", p.department); option = attrs.get("option", p.option)
        if school and school.university_id != p.university_id:
            raise serializers.ValidationError({"school":"School does not belong to your university."})
        if department and (not school or department.school_id != school.id):
            raise serializers.ValidationError({"department":"Department does not belong to selected school."})
        if option and (not department or option.department_id != department.id):
            raise serializers.ValidationError({"option":"Option does not belong to selected department."})
        return attrs
