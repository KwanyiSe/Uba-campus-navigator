import csv
from datetime import datetime
from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from campus.models import Building, University
from accounts.models import Profile, School, Department, Option, Notification
from accounts.notifications import notify_profile, notify_profiles
from .models import *
from .form_b_parser import parse_form_b
from campus.geofencing import point_in_polygon, valid_polygon
from .serializers import *

def profile(request):
    return getattr(request.user, "profile", None)

def staff(p):
    return p and p.role in {"cc", "lecturer", "school_admin", "admin"}

def admin_scope(p):
    return p and p.role in {"school_admin", "admin"}

def cc_assignment_for_session(p, session):
    return bool(
        p and p.role == "cc" and session.option_id and
        ClassCoordinatorAssignment.objects.filter(
            coordinator=p,
            option_id=session.option_id,
            level=session.level,
            active=True,
        ).exists()
    )

def expire_due_class_sessions():
    """Close sessions whose scheduled end time has passed.

    This is intentionally server-side. Attendance never trusts the client or the
    CC to press End Class. The helper is called by class/attendance APIs so a
    due session is persisted as completed as soon as the system touches it.
    """
    now = timezone.localtime()
    today = now.date()
    due = ClassSession.objects.filter(
        status__in={"scheduled", "active"},
    ).filter(
        Q(session_date__lt=today) |
        Q(session_date=today, end_time__lte=now.time())
    )
    sessions = list(due.select_related("course", "option"))
    if not sessions:
        return 0

    completed_at = now
    for session in sessions:
        session.status = "completed"
        session.ended_at = session.ended_at or completed_at
        session.save(update_fields=["status", "ended_at"])

        recipients = Profile.objects.filter(
            university=session.course.university,
            option=session.option,
            level=session.level,
            user__is_active=True,
        )
        notify_profiles(
            recipients,
            "Class ended automatically",
            f"{session.course.code} — {session.course.name} has ended because its scheduled end time was reached.",
            "class",
            f"/class/?id={session.id}",
        )
    return len(sessions)


def can_manage_session(p, session):
    if not p or not session:
        return False
    if p.role in {"school_admin", "admin"}:
        return session.course.university_id == p.university_id
    if p.role == "cc":
        return cc_assignment_for_session(p, session)
    if p.role == "lecturer":
        return session.lecturer_id == p.id or session.course.lecturer_id == p.user_id
    return False

class CourseListView(generics.ListAPIView):
    serializer_class=CourseSerializer; permission_classes=[AllowAny]
    def get_queryset(self):
        qs=Course.objects.filter(active=True).select_related("department","lecturer","lecturer__profile")
        uni=self.request.GET.get("university")
        return qs.filter(university__short_name__iexact=uni) if uni else qs

class ClassSessionListView(generics.ListAPIView):
    serializer_class=ClassSessionSerializer; permission_classes=[AllowAny]
    def get_queryset(self):
        expire_due_class_sessions()
        qsClassSession.objects.filter(active=True).select_related("course","building","option")
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
    serializer_class = ClassSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        expire_due_class_sessions()
        p = profile(self.request)
        if not p:
            return ClassSession.objects.none()

        qs = ClassSession.objects.filter(active=True).select_related(
            "course", "building", "option", "form_b"
        )

        if p.role == "cc":
            assignments = ClassCoordinatorAssignment.objects.filter(
                coordinator=p, active=True
            ).values("option_id", "level")
            from django.db.models import Q as DQ
            scope = DQ(pk__in=[])
            for assignment in assignments:
                scope |= DQ(
                    option_id=assignment["option_id"],
                    level=assignment["level"],
                )
            return qs.filter(scope)

        if p.role == "lecturer":
            return qs.filter(
                Q(lecturer=p) | Q(course__lecturer=p.user)
            ).distinct()

        if p.role in {"school_admin", "admin"}:
            return qs.filter(course__university=p.university)

        return qs.filter(option=p.option, level=p.level)

class HallAvailabilityView(APIView):
    permission_classes=[AllowAny]
    def get(self,request):
        expire_due_class_sessions()
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
        expire_due_class_sessions()
        uni=University.objects.filter(active=True,short_name__iexact=request.GET.get("university","")).first() or University.objects.filter(active=True).first()
        if not uni:return Response({"university":None,"buildings":0,"active_sessions":[],"activities":[]})
        sessions=ClassSession.objects.filter(course__university=uni,status="active",session_date=timezone.localdate()).select_related("course","building","option")
        return Response({"university":{"id":uni.id,"name":uni.name,"short_name":uni.short_name},"buildings":Building.objects.filter(university=uni).count(),"active_sessions":ClassSessionSerializer(sessions,many=True).data,"activities":CampusActivitySerializer(CampusActivity.objects.filter(university=uni,active=True)[:10],many=True).data})

class CCWorkspaceView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        p=profile(request)
        if not p or p.role!="cc":
            return Response({"detail":"Class Coordinator access required."},403)

        assignments=list(
            ClassCoordinatorAssignment.objects.filter(
                coordinator=p,active=True
            ).select_related("option","option__department").values(
                "id","option_id","option__name","option__department_id",
                "option__department__name","level"
            )
        )
        pairs={(x["option_id"],x["level"]) for x in assignments}

        forms=FormB.objects.filter(
            university=p.university,
            option__coordinator_assignments__coordinator=p,
            option__coordinator_assignments__active=True,
        ).select_related(
            "academic_year","semester","department","option"
        ).prefetch_related("courses__course").distinct().order_by("-uploaded_at")[:50]

        classes=ClassSession.objects.filter(
            course__university=p.university,active=True
        ).select_related("course","building","option","form_b").order_by(
            "session_date","start_time"
        )
        classes=[x for x in classes if (x.option_id,x.level) in pairs]

        return Response({
            "profile":{
                "id":p.id,
                "name":p.display_name(),
                "university":p.university.name,
            },
            "assignments":assignments,
            "academic_years":AcademicYearSerializer(
                AcademicYear.objects.filter(active=True),many=True
            ).data,
            "semesters":SemesterSerializer(
                Semester.objects.select_related("academic_year").filter(active=True),many=True
            ).data,
            "form_bs":FormBSerializer(
                forms,many=True,context={"request":request}
            ).data,
            "classes":ClassSessionSerializer(classes,many=True).data,
        })


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
        notify_profile(
            target,
            "Role updated",
            f"You have been appointed as {target.get_role_display()}. Your UNIMAP tools have been updated.",
            "staff",
            "/classes/" if role == "cc" else "/classes/",
        )
        return Response({"message":"Staff appointment updated.","role":role})

class ClassSessionCreateView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self,request):
        p=profile(request)
        course=Course.objects.filter(id=request.data.get("course")).select_related("university").first()
        option=Option.objects.filter(id=request.data.get("option")).first()
        form_b=FormB.objects.filter(id=request.data.get("form_b")).first() if request.data.get("form_b") else None
        if not p or not course or not option:
            return Response({"detail":"Course and option are required."},400)

        try:
            level=int(request.data.get("level"))
        except (TypeError,ValueError):
            return Response({"detail":"A valid level is required."},400)

        if p.role=="cc":
            assigned=ClassCoordinatorAssignment.objects.filter(
                coordinator=p,option=option,level=level,active=True
            ).exists()
            if not assigned:
                return Response({"detail":"You are not assigned to this cohort."},403)
            if not form_b:
                return Response({"detail":"Select the published Form B for this cohort before creating a class."},400)
            if form_b.status!="published":
                return Response({"detail":"The selected Form B must be published before creating a class."},400)
            if form_b.option_id!=option.id or form_b.level!=level:
                return Response({"detail":"The Form B does not match this cohort."},400)
            if not form_b.courses.filter(course=course).exists():
                return Response({"detail":"The selected course is not on this Form B."},400)
        elif p.role=="lecturer":
            if course.lecturer_id!=p.user_id:
                return Response({"detail":"Course is not assigned to you."},403)
        elif p.role not in {"school_admin","admin"}:
            return Response({"detail":"Not allowed."},403)

        if course.university_id!=p.university_id or option.department.school.university_id!=p.university_id:
            return Response({"detail":"This class is outside your university scope."},403)

        data=request.data.copy()
        data["created_by"]=request.user.id
        data["coordinator"]=p.id if p.role=="cc" else data.get("coordinator")
        data["lecturer"]=p.id if p.role=="lecturer" else data.get("lecturer")
        serializer=ClassSessionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        obj=serializer.save()
        recipients = Profile.objects.filter(
            university=p.university, option=obj.option, level=obj.level, user__is_active=True
        )
        notify_profiles(
            recipients,
            "New class scheduled",
            f"{obj.course.code} — {obj.course.name} is scheduled for {obj.session_date} at {obj.start_time}.",
            "class",
            f"/class/?id={obj.id}",
        )
        return Response(ClassSessionSerializer(obj).data,201)

class ClassSessionActionView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self,request,pk):
        expire_due_class_sessions()
        p=profile(request)
        obj=ClassSession.objects.select_related("course","option").filter(pk=pk).first()
        if not obj or not can_manage_session(p,obj):
            return Response({"detail":"You do not have permission to manage this class."},403)

        action=request.data.get("action")
        now=timezone.now()
        if action=="start":
            if obj.status!="scheduled":
                return Response({"detail":"Only scheduled classes can be started."},400)
            now_local = timezone.localtime(now)
            if obj.session_date != now_local.date():
                return Response({"detail":"A class can only be started on its scheduled date."},400)
            if now_local.time() < obj.start_time:
                return Response({"detail":f"This class is scheduled to start at {obj.start_time}."},400)
            if now_local.time() >= obj.end_time:
                obj.status="completed"; obj.ended_at=now
                obj.save(update_fields=["status","ended_at"])
                return Response({"detail":"This class has already passed its scheduled end time."},400)
            obj.status="active"; obj.started_at=now
            obj.save(update_fields=["status","started_at"])
            recipients = Profile.objects.filter(university=p.university, option=obj.option, level=obj.level, user__is_active=True)
            notify_profiles(recipients, "Class started", f"{obj.course.code} — {obj.course.name} has started. Open Classes to view it.", "class", f"/class/?id={obj.id}")
        elif action=="end":
            if obj.status!="active":
                return Response({"detail":"Only active classes can be ended."},400)
            obj.status="completed"; obj.ended_at=now
            obj.save(update_fields=["status","ended_at"])
            recipients = Profile.objects.filter(university=p.university, option=obj.option, level=obj.level, user__is_active=True)
            notify_profiles(recipients, "Class ended", f"{obj.course.code} — {obj.course.name} has ended.", "class", f"/class/?id={obj.id}")
        elif action=="cancel":
            if obj.status in {"completed","cancelled"}:
                return Response({"detail":"This class can no longer be cancelled."},400)
            obj.status="cancelled"
            obj.save(update_fields=["status"])
            recipients = Profile.objects.filter(university=p.university, option=obj.option, level=obj.level, user__is_active=True)
            notify_profiles(recipients, "Class cancelled", f"{obj.course.code} — {obj.course.name} has been cancelled.", "class", "/classes/")
        else:
            return Response({"detail":"Action must be start, end or cancel."},400)
        return Response(ClassSessionSerializer(obj).data)

class AttendanceListView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        p=profile(request); s=ClassSession.objects.filter(pk=pk).first()
        if not s or not can_manage_session(p,s):return Response({"detail":"Not allowed."},403)
        students=Profile.objects.filter(university=s.course.university,option=s.option,level=s.level).select_related("user")
        existing={a.student_id:a for a in AttendanceRecord.objects.filter(session=s)}
        rows=[]
        for st in students:
            a=existing.get(st.id); rows.append({"student_id":st.id,"name":st.display_name(),"matric_number":st.matric_number,"status":a.status if a else "absent","verification_method":a.verification_method if a else None})
        return Response(rows)
    def patch(self,request,pk):
        p=profile(request); s=ClassSession.objects.filter(pk=pk).first()
        if not s or not can_manage_session(p,s):return Response({"detail":"Not allowed."},403)
        st=Profile.objects.filter(pk=request.data.get("student")).first(); statusv=request.data.get("status")
        if not st or statusv not in {"present","absent"}:return Response({"detail":"Invalid attendance update."},400)
        a,_=AttendanceRecord.objects.update_or_create(session=s,student=st,defaults={"status":statusv,"verification_method":"manual"})
        return Response(AttendanceSerializer(a).data)

class AttendanceDownloadView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,pk):
        p=profile(request); s=ClassSession.objects.filter(pk=pk).first()
        if not s or not can_manage_session(p,s):return Response({"detail":"Not allowed."},403)
        resp=HttpResponse(content_type="text/csv");resp["Content-Disposition"]=f'attachment; filename="attendance_{s.id}.csv"'
        w=csv.writer(resp);w.writerow(["Name","Matric Number","Status","Verification"])
        for a in AttendanceRecord.objects.filter(session=s).select_related("student"):w.writerow([a.student.display_name(),a.student.matric_number,a.status,a.verification_method])
        return resp

class MarkAttendanceView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,pk):
        expire_due_class_sessions()
        p=profile(request)
        s=ClassSession.objects.select_related("course","building","form_b").filter(pk=pk,status="active",session_date=timezone.localdate()).first()
        if not s or not p:return Response({"detail":"Class is not currently active."},400)
        now_local = timezone.localtime()
        if now_local.time() >= s.end_time:
            s.status = "completed"
            s.ended_at = s.ended_at or now_local
            s.save(update_fields=["status", "ended_at"])
            return Response({"detail":"Attendance is closed because the scheduled class end time has been reached."},400)
        if p.option_id!=s.option_id or p.level!=s.level:return Response({"detail":"You are not in this class cohort."},403)
        if not Enrollment.objects.filter(student=p,course=s.course,active=True).filter(form_b=s.form_b).exists() and not Enrollment.objects.filter(student=p,course=s.course,active=True,form_b__isnull=True).exists():
            return Response({"detail":"You are not enrolled in this course."},403)
        if not s.building:
            return Response({"detail":"This class has no building assigned, so attendance cannot be automatically verified."},409)
        polygon=s.building.geofence
        if not valid_polygon(polygon):
            return Response({"detail":"This building does not have a valid campus geofence yet."},409)
        try:
            lat=float(request.data.get("latitude")); lng=float(request.data.get("longitude"))
            accuracy=float(request.data.get("accuracy")) if request.data.get("accuracy") not in (None,"") else None
        except (TypeError,ValueError):
            return Response({"detail":"latitude and longitude are required."},400)
        if accuracy is not None and accuracy < 0:
            return Response({"detail":"Invalid GPS accuracy."},400)
        if not point_in_polygon(lat,lng,polygon):
            notify_profile(p, "Attendance not recorded", f"You are outside the attendance area for {s.course.code}. Move inside the class building and try again.", "attendance", f"/class/?id={s.id}")
            return Response({"detail":"You are outside the attendance geofence for this class."},403)
        a,_=AttendanceRecord.objects.update_or_create(session=s,student=p,defaults={"status":"present","verification_method":"automatic","latitude":lat,"longitude":lng,"accuracy":accuracy,"verified_at":timezone.now()})
        notify_profile(p, "Attendance recorded", f"Your attendance for {s.course.code} — {s.course.name} was successfully verified.", "attendance", f"/class/?id={s.id}")
        return Response({"message":"Attendance marked automatically.","attendance":AttendanceSerializer(a).data})

class AcademicYearListView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request): return Response(AcademicYearSerializer(AcademicYear.objects.all(),many=True).data)
    def post(self,request):
        p=profile(request)
        if not p or p.role not in {"school_admin","admin"}: return Response({"detail":"School Admin or University Admin required."},403)
        ser=AcademicYearSerializer(data=request.data); ser.is_valid(raise_exception=True); return Response(ser.data if False else AcademicYearSerializer(ser.save()).data,201)

class SemesterListView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        qs=Semester.objects.select_related("academic_year").all()
        ay=request.GET.get("academic_year")
        if ay: qs=qs.filter(academic_year_id=ay)
        return Response(SemesterSerializer(qs,many=True).data)
    def post(self,request):
        p=profile(request)
        if not p or p.role not in {"school_admin","admin"}: return Response({"detail":"School Admin or University Admin required."},403)
        ser=SemesterSerializer(data=request.data); ser.is_valid(raise_exception=True); return Response(SemesterSerializer(ser.save()).data,201)

class FormBListCreateView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request):
        p=profile(request)
        if not p:return Response([],200)
        qs=FormB.objects.filter(university=p.university).select_related("academic_year","semester","department","option").prefetch_related("courses__course")
        if p.role=="cc": qs=qs.filter(option__coordinator_assignments__coordinator=p, option__coordinator_assignments__active=True).distinct()
        return Response(FormBSerializer(qs[:100],many=True,context={"request":request}).data)
    @transaction.atomic
    def post(self,request):
        p=profile(request)
        if not p or p.role not in {"cc","school_admin","admin"}: return Response({"detail":"Not allowed."},403)
        option=Option.objects.filter(pk=request.data.get("option"),department_id=request.data.get("department")).first()
        semester=Semester.objects.filter(pk=request.data.get("semester")).select_related("academic_year").first()
        department=option.department if option else None
        if not option or not semester:return Response({"detail":"department, option and semester are required."},400)
        if p.role=="cc" and not ClassCoordinatorAssignment.objects.filter(coordinator=p,option=option,level=int(request.data.get("level")),active=True).exists():return Response({"detail":"You are not assigned to this cohort."},403)
        if department.school.university_id!=p.university_id or semester.academic_year_id is None:return Response({"detail":"Invalid academic scope."},400)
        uploaded=request.FILES.get("file")
        if not uploaded:return Response({"detail":"Form B file is required."},400)
        try: courses=parse_form_b(uploaded,uploaded.name)
        except ValueError as exc:return Response({"detail":str(exc)},400)
        form=FormB.objects.create(university=p.university,academic_year=semester.academic_year,semester=semester,department=department,option=option,level=int(request.data.get("level")),title=request.data.get("title","") or uploaded.name,file=uploaded,uploaded_by=request.user)
        for pos,item in enumerate(courses):
            course,_=Course.objects.get_or_create(university=p.university,code=item["code"],defaults={"name":item["name"],"department":department})
            updates=[]
            if not course.name or course.name==course.code: course.name=item["name"]; updates.append("name")
            if not course.department_id: course.department=department; updates.append("department")
            if updates: course.save(update_fields=updates)
            FormBCourse.objects.create(form_b=form,course=course,source_code=item["code"],source_name=item["name"],position=pos)
        form.parsed_at=timezone.now(); form.save(update_fields=["parsed_at"])
        return Response(FormBSerializer(form,context={"request":request}).data,201)

class FormBPublishView(APIView):
    permission_classes=[IsAuthenticated]
    @transaction.atomic
    def post(self,request,pk):
        p=profile(request); form=FormB.objects.select_related("option","department","academic_year","semester").prefetch_related("courses__course").filter(pk=pk).first()
        if not form or not p:return Response({"detail":"Form B not found."},404)
        allowed=p.role in {"school_admin","admin"} or (p.role=="cc" and ClassCoordinatorAssignment.objects.filter(coordinator=p,option=form.option,level=form.level,active=True).exists())
        if not allowed:return Response({"detail":"Not allowed."},403)
        students=Profile.objects.filter(university=form.university,school=form.department.school,department=form.department,option=form.option,level=form.level,user__is_active=True)
        created=0
        for entry in form.courses.select_related("course"):
            for student in students:
                _,made=Enrollment.objects.get_or_create(student=student,course=entry.course,form_b=form,defaults={"active":True})
                created += int(made)
        form.status="published"; form.save(update_fields=["status"])
        notify_profiles(
            students,
            "Courses updated",
            f"Your {form.option.name} Level {form.level} course list for {form.semester.get_name_display()} has been published.",
            "form_b",
            "/classes/",
        )
        return Response({"message":"Form B published and enrollments generated.","form_b_id":form.id,"students_matched":students.count(),"enrollments_created":created})

@method_decorator(csrf_exempt, name="dispatch")
class NotificationListView(APIView):
    permission_classes=[IsAuthenticated]

    def get(self,request):
        p=profile(request)
        if not p:return Response({"unread":0,"notifications":[]})
        qs=Notification.objects.filter(recipient=p)[:100]
        return Response({
            "unread":Notification.objects.filter(recipient=p,read_at__isnull=True).count(),
            "notifications":[{
                "id":n.id,"type":n.notification_type,"title":n.title,"body":n.body,
                "link":n.link,"created_at":n.created_at,"read":n.read_at is not None
            } for n in qs]
        })

    def patch(self,request):
        p=profile(request)
        ids=request.data.get("ids")
        qs=Notification.objects.filter(recipient=p,read_at__isnull=True)
        if ids:
            if not isinstance(ids,list): ids=[ids]
            qs=qs.filter(id__in=ids)
        count=qs.update(read_at=timezone.now())
        return Response({"marked_read":count})


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
        recipients=Profile.objects.filter(university=p.university,user__is_active=True)
        if post.audience=="school": recipients=recipients.filter(school=post.school)
        elif post.audience=="department": recipients=recipients.filter(department=post.department)
        elif post.audience=="option": recipients=recipients.filter(option=post.option)
        elif post.audience=="level": recipients=recipients.filter(option=post.option,level=post.level)
        recipients=recipients.exclude(pk=p.pk)
        notify_profiles(recipients, "New News post", post.title, "news", "/campus-now/")
        return Response(NewsPostSerializer(post).data,201)
