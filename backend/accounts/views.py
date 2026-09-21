from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from campus.models import University
from .models import School, Department
from .serializers import (
    RegisterSerializer,
    ProfileUpdateSerializer
)




class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        
        return Response({
            "username": request.user.username,

            "role": profile.role,

            "university": (
                profile.university.name
                if profile.university else None
            ),

            "university_id": (
                profile.university.id
                if profile.university else None
            ),

            "school": (
                profile.school.name
                if profile.school else None
            ),

            "school_id": (
                profile.school.id
                if profile.school else None
            ),

            "department": (
                profile.department.name
                if profile.department else None
            ),

            "department_id": (
                profile.department.id
                if profile.department else None
            ),

            "matric_number": profile.matric_number,
            "admission_year": profile.admission_year,
            "level": profile.level
        })
     
        
## now lets create the apis for fontend to use..
class UniversityListView(APIView):
    """ the university list view"""

    def get(self, request):

        universities = University.objects.all()
        data = [
            {
                "id": university.id,
                "name": university.name,
                "short_name": university.short_name
            }
            for university in universities
        ]
        return Response(data)

class SchoolListView(APIView):
    """school listview"""
    def get(self, request):

        university_id = request.GET.get("university")

        if not university_id:
            return Response(
                {"error": "university parameter is required"},
                status=400
            )

        schools = School.objects.filter( university_id=university_id)

        data = [ {"id": school.id,"name": school.name}for school in schools]

        return Response(data)
    
    
class DepartmentListView(APIView):

    def get(self, request):

        school_id = request.GET.get("school")

        if not school_id:
            return Response(
                {"error": "school parameter is required"},
                status=400
            )

        departments = Department.objects.filter(
            school_id=school_id
        )

        data = [
            {
                "id": department.id,
                "name": department.name
            }
            for department in departments
        ]
        return Response(data)
    
    
class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):

        profile = request.user.profile

        serializer = ProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=True
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        #returning the reponse with the updated data to aviodd another api call (: kwanyi..
        return Response({
            "message": "Profile updated successfully",

            "school": (
                profile.school.name
                if profile.school else None
            ),

            "department": (
                profile.department.name
                if profile.department else None
            ),

            "level": profile.level,

            "matric_number": profile.matric_number
        })