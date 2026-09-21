import csv
from datetime import datetime
from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from campus.models import Building, University
from accounts.models import Profile, School, Department, Option
from .models import Course, ClassSession, Enrollment, AttendanceRecord, CampusActivity, Timetable, ClassCoordinatorAssignment, NewsPost, NewsAttachment
from .serializers import *

def profile(request): return getattr(request.user, "profile", None)
def staff(p): return p and p.role in {"cc","lecturer","school_admin","admin"}
def admin_scope(p): return p and p.role in {"school_admin","admin"}

class CourseListView(generics.ListAPIView):
    serializer_class=CourseSerializer; permission_classes=[AllowAny]
    def get_queryset(self):
        qs=Course.objects.filter(active=True).select_related("department","lecturer","lecturer__profile")
        uni=self.request.GET.get("university")
        return qs.filter(university__short_name__iexact=uni) if uni else qs

class ClassSessionListView(generics.ListAPIView):
    serializer_class=ClassSessionSerializer; permission_classes=[AllowAny]
    def get_queryset(self):
        qs=ClassSession.objects.filter(active=True).select_related("course","building","option")
        uni=self.request.GET.get("university")
        return qs.filter(course__university__short_name__iexact=uni) if uni else qs

class MyClassesView(generics.ListAPIView):
    serializer_class=EnrollmentSerializer; permission_classes=[IsAuthenticated]
    def get_queryset(self):
        p=profile(self.request); return Enrollment.objects.filter(student=p,active=True).select_related("course") if p else Enrollment.objects.none()

class MyAttendanceView(generics.ListAPIView):
    serializer_class=AttendanceSerializer; permission_classes=[IsAuthenticated]
    def get_queryset(self):
        p=profile(self.request); return AttendanceRecord.objects.filter(student=p).select_related("session__course") if p else AttendanceRecord.objects.none()

class MyScheduleView(generics.ListAPIView):
    serializer_class=ClassSessionSerializer; permission_classes=[IsAuthenticated]
    def get_queryset(self):
        p=profile(self.request)
        if not p: return ClassSession.objects.none()
        return ClassSession.objects.filter(option=p.option,level=p.level,active=True).select_related("course","building","option")

class HallAvailabilityView(APIView):
    permission_classes=[AllowAny]
    def get(self,request):
        uni=University.objects.filter(active=True,short_name__iexact=request.GET.get("university","")).first() or University.objects.filter(active=True).first()
        if not uni: return Response([])
        now=timezone.localtime(); halls=Building.objects.filter(university=uni).filter(Q(category__icontains="hall")|Q(category__icontains="lecture")|Q(category__icontains="theatre"))
        sessions=ClassSession.objects.filter(course__university=uni,building__in=halls,status="active",session_date=timezone.localdate()).select_related("course","building")
        active={s.building_id:s for s in sessions}
        return Response([{"id":h.id,"name":h.name,"category":h.category,"floor":h.floor,"capacity":h.capacity,"status":"in_use" if h.id in active else h.status,"building":h.name,"current_class":active[h.id].course.code if h.id in active else None,"photo":h.photo.url if h.photo else None} for h in halls])

class CampusActivityListView(APIView):
    permission_classes=[AllowAny]
    def get(self,request):
        uni=University.objects.filter(active=True,short_name__iexact=request.GET.get("university","")).first() or University.objects.filter(active=True).first()
        if not uni:return Response([])
        return Response(CampusActivitySerializer(CampusActivity.objects.filter(university=uni,active=True)[:10],many=True).data)

class CampusOverviewView(APIView):
    permission_classes=[AllowAny]
    def get(self,request):
        uni=University.objects.filter(active=True,short_name__iexact=request.GET.get("university","")).first() or University.objects.filter(active=True).first()
        if not uni:return Response({"university":None,"buildings":0,"active_sessions":[],"activities":[]})
        sessions=ClassSession.objects.filter(course__university=uni,status="active",session_date=timezone.localdate()).select_related("course","building","option")
        return Response({"university":{"id":uni.id,"name":uni.name,"short_name":uni.short_name},"buildings":Building.objects.filter(university=uni).count(),"active_sessions":ClassSessionSerializer(sessions,many=True).data,"activities":CampusActivitySerializer(CampusActivity.objects.filter(university=uni,active=True)[:10],many=True).data})

class TimetableView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        p=profile(request)
        qs=Timetable.objects.filter(university=p.university,active=True) if p else Timetable.objects.none()
        return Response(TimetableSerializer(qs,many=True).data)
    def post(self,request):
        p=profile(request)
        if not admin_scope(p) and not (p and p.role=="cc"): return Response({"detail":"Not allowed."},403)
        s=TimetableSerializer(data=request.data); s.is_valid(raise_exception=True)
        obj=s.save(uploaded_by=request.user,university=p.university); return Response(TimetableSerializer(obj).data,201)

class StaffDirectoryView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        p=profile(request)
        if not admin_scope(p): return Response({"detail":"School Admin or University Admin required."},403)
        qs=Profile.objects.filter(university=p.university).select_related("user","school","department","option")
        if p.role=="school_admin": qs=qs.filter(school=p.school)
        return Response([{"id":x.id,"user_id":x.user_id,"name":x.display_name(),"email":x.user.email,"role":x.role,"school_id":x.school_id,"department_id":x.department_id,"option_id":x.option_id,"level":x.level} for x in qs])

class StaffAssignmentView(APIView):
    permission_classes=[IsAuthenticated]
    @transaction.atomic
    def post(self,request):
        actor=profile(request); target=Profile.objects.filter(id=request.data.get("profile")).first()
        role=request.data.get("role")
        if not admin_scope(actor) or not target or target.university_id!=actor.university_id or role not in {"lecturer","cc"}: return Response({"detail":"Invalid appointment."},400)
        if actor.role=="school_admin" and target.school_id!=actor.school_id:return Response({"detail":"User is outside your school."},403)
        if role=="cc":
            option=Option.objects.filter(id=request.data.get("option"),department__school=target.school).first()
            level=request.data.get("level")
            if not option or level is None:return Response({"detail":"CC requires option and level."},400)
            ClassCoordinatorAssignment.objects.update_or_create(option=option,level=int(level),defaults={"coordinator":target,"active":True})
        target.role=role; target.save(update_fields=["role"])
        return Response({"message":"Staff appointment updated.","role":role})

class ClassSessionCreateView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request):
        p=profile(request); course=Course.objects.filter(id=request.data.get("course")).first(); option=Option.objects.filter(id=request.data.get("option")).first()
        if not p or not course or not option:return Response({"detail":"Course and option are required."},400)
        if p.role=="cc" and not ClassCoordinatorAssignment.objects.filter(coordinator=p,option=option,level=request.data.get("level"),active=True).exists(): return Response({"detail":"You are not assigned to this cohort."},403)
        if p.role=="lecturer" and course.lecturer_id!=p.user_id:return Response({"detail":"Course is not assigned to you."},403)
        if p.role not in {"cc","lecturer","school_admin","admin"}:return Response({"detail":"Not allowed."},403)
        data=request.data.copy(); data["created_by"]=request.user.id; data["coordinator"]=p.id if p.role=="cc" else data.get("coordinator"); data["lecturer"]=p.id if p.role=="lecturer" else data.get("lecturer")
        s=ClassSessionSerializer(data=data); s.is_valid(raise_exception=True); obj=s.save()
        return Response(ClassSessionSerializer(obj).data,201)

class ClassSessionActionView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,pk):
        p=profile(request); obj=ClassSession.objects.filter(pk=pk).first()
        if not obj or not p or p.role not in {"cc","lecturer","school_admin","admin"}:return Response({"detail":"Not allowed."},403)
        action=request.data.get("action"); now=timezone.now()
        if action=="start": obj.status="active";obj.started_at=now
        elif action=="end": obj.status="completed";obj.ended_at=now
        elif action=="cancel": obj.status="cancelled"
        else:return Response({"detail":"Action must be start, end or cancel."},400)
        obj.save(); return Response(ClassSessionSerializer(obj).data)

class AttendanceListView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        p=profile(request); s=ClassSession.objects.filter(pk=pk).first()
        if not s or not staff(p):return Response({"detail":"Not allowed."},403)
        students=Profile.objects.filter(university=s.course.university,option=s.option,level=s.level).select_related("user")
        existing={a.student_id:a for a in AttendanceRecord.objects.filter(session=s)}
        rows=[]
        for st in students:
            a=existing.get(st.id); rows.append({"student_id":st.id,"name":st.display_name(),"matric_number":st.matric_number,"status":a.status if a else "absent","verification_method":a.verification_method if a else None})
        return Response(rows)
    def patch(self,request,pk):
        p=profile(request); s=ClassSession.objects.filter(pk=pk).first()
        if not s or not staff(p):return Response({"detail":"Not allowed."},403)
        st=Profile.objects.filter(pk=request.data.get("student")).first(); statusv=request.data.get("status")
        if not st or statusv not in {"present","absent"}:return Response({"detail":"Invalid attendance update."},400)
        a,_=AttendanceRecord.objects.update_or_create(session=s,student=st,defaults={"status":statusv,"verification_method":"manual"})
        return Response(AttendanceSerializer(a).data)

class AttendanceDownloadView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        p=profile(request); s=ClassSession.objects.filter(pk=pk).first()
        if not s or not staff(p):return Response({"detail":"Not allowed."},403)
        resp=HttpResponse(content_type="text/csv");resp["Content-Disposition"]=f'attachment; filename="attendance_{s.id}.csv"'
        w=csv.writer(resp);w.writerow(["Name","Matric Number","Status","Verification"])
        for a in AttendanceRecord.objects.filter(session=s).select_related("student"):w.writerow([a.student.display_name(),a.student.matric_number,a.status,a.verification_method])
        return resp

class MarkAttendanceView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,pk):
        p=profile(request); s=ClassSession.objects.filter(pk=pk,status="active",session_date=timezone.localdate()).first()
        if not s or not p:return Response({"detail":"Class is not currently active."},400)
        if p.option_id!=s.option_id or p.level!=s.level:return Response({"detail":"You are not in this class cohort."},403)
        if not request.data.get("location_verified",False):
            return Response({"detail":"Automatic attendance verification is not configured until this class location has a campus geofence."},409)
        a,_=AttendanceRecord.objects.update_or_create(session=s,student=p,defaults={"status":"present","verification_method":"automatic"})
        return Response(AttendanceSerializer(a).data)

class NewsFeedView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        p=profile(request); qs=NewsPost.objects.filter(
            university=p.university,
            active=True,
        ).select_related(
            "author",
            "school",
            "department",
            "option",
        ).prefetch_related("attachments")
        typ=request.GET.get("type")
        if typ in {"study_group","campus_news"}:qs=qs.filter(post_type=typ)
        scope=request.GET.get("scope","all")
        if scope=="school":qs=qs.filter(Q(audience="university")|Q(audience="school",school=p.school)|Q(audience="department",department=p.department)|Q(audience="option",option=p.option)|Q(audience="level",option=p.option,level=p.level))
        elif scope=="department":qs=qs.filter(Q(audience="university")|Q(audience="department",department=p.department)|Q(audience="option",option=p.option)|Q(audience="level",option=p.option,level=p.level))
        elif scope=="option":qs=qs.filter(Q(audience="university")|Q(audience="option",option=p.option)|Q(audience="level",option=p.option,level=p.level))
        elif scope=="level":qs=qs.filter(Q(audience="university")|Q(audience="level",option=p.option,level=p.level))
        return Response(NewsPostSerializer(qs[:50],many=True).data)

class NewsCreateView(APIView):
    permission_classes=[IsAuthenticated]
    @transaction.atomic
    def post(self,request):
        p=profile(request); typ=request.data.get("post_type","study_group"); aud=request.data.get("audience","university")
        if not p:return Response({"detail":"Profile required."},403)
        if typ=="campus_news" and p.role not in {"cc","lecturer","school_admin","admin"}:return Response({"detail":"Only appointed staff can publish Campus News."},403)
        if typ not in {"study_group","campus_news"}:return Response({"detail":"Invalid post type."},400)
        if p.role in {"cc","lecturer"} and aud=="university":return Response({"detail":"Official staff Campus News must stay within your academic scope."},400)
        data=request.data.copy(); data["university"]=p.university_id;data["author"]=p.id
        for key,val in [("school",p.school_id),("department",p.department_id),("option",p.option_id)]:
            if not data.get(key): data[key]=val
        s=NewsPostSerializer(data=data);s.is_valid(raise_exception=True);post=s.save()
        for f in request.FILES.getlist("attachments"):
            NewsAttachment.objects.create(post=post,file=f,original_name=f.name)
        return Response(NewsPostSerializer(post).data,201)
