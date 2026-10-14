from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView
from campus.models import University
from .models import School, Department, Option, Profile
from .serializers import RegisterSerializer, ProfileUpdateSerializer


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class ProfileView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    authentication_classes = [SessionAuthentication, JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        p = getattr(request.user, "profile", None)
        if p is None:
            u = University.objects.filter(active=True).first()
            if not u: return Response({"detail":"No active university is configured."}, status=503)
            p = Profile.objects.create(user=request.user, university=u)
        return Response(profile_payload(p))

    def patch(self, request):
        profile = getattr(request.user, "profile", None)
        if profile is None:
            university = University.objects.filter(active=True).first()
            if university is None:
                return Response({"detail": "No active university is configured."}, status=503)
            profile = Profile.objects.create(user=request.user, university=university)
        s = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        s.is_valid(raise_exception=True); s.save()
        return Response(profile_payload(s.instance))


def profile_payload(p):
    return {
        "username": p.user.username, "full_name": p.display_name(), "email": p.user.email,
        "role": p.role, "profile_picture": p.profile_picture.url if p.profile_picture else None,
        "university": p.university.name if p.university else None, "university_id": p.university_id,
        "university_short_name": p.university.short_name if p.university else None,
        "school": p.school.name if p.school else None, "school_id": p.school_id,
        "department": p.department.name if p.department else None, "department_id": p.department_id,
        "option": p.option.name if p.option else None, "option_id": p.option_id,
        "matric_number": p.matric_number, "admission_year": p.admission_year, "level": p.level,
    }


class UniversityListView(APIView):
    def get(self, request):
        return Response([{"id":u.id,"name":u.name,"short_name":u.short_name,"logo":u.logo.url if u.logo else None} for u in University.objects.filter(active=True).order_by("name")])


class SchoolListView(APIView):
    def get(self, request):
        uid=request.GET.get("university")
        if not uid: return Response({"error":"university parameter is required"}, status=400)
        return Response([{"id":s.id,"name":s.name,"logo":s.logo.url if s.logo else None} for s in School.objects.filter(university_id=uid).order_by("name")])


class DepartmentListView(APIView):
    def get(self, request):
        sid=request.GET.get("school")
        if not sid: return Response({"error":"school parameter is required"}, status=400)
        return Response([{"id":d.id,"name":d.name,"logo":d.logo.url if d.logo else None} for d in Department.objects.filter(school_id=sid).order_by("name")])


class OptionListView(APIView):
    def get(self, request):
        did=request.GET.get("department")
        if not did: return Response({"error":"department parameter is required"}, status=400)
        return Response([{"id":o.id,"name":o.name,"code":o.code} for o in Option.objects.filter(department_id=did, active=True).order_by("name")])


class SchoolOptionListView(APIView):
    def get(self, request):
        sid=request.GET.get("school")
        if not sid: return Response({"error":"school parameter is required"}, status=400)
        return Response([{"id":o.id,"name":o.name,"code":o.code,"department_id":o.department_id} for o in Option.objects.filter(department__school_id=sid, active=True).order_by("name")])


class ProfileUpdateView(ProfileView):
    pass
