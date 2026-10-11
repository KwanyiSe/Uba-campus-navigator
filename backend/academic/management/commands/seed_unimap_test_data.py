from django.core.management.base import BaseCommand
from campus.models import University, Building
from accounts.models import School, Department, Option
from academic.models import AcademicYear, Semester


class Command(BaseCommand):
    help = "Create non-destructive UNIMAP test hierarchy and academic records."

    def handle(self, *args, **options):
        uni = University.objects.filter(short_name__iexact="UBa").first() or University.objects.filter(active=True).first()
        if not uni:
            self.stderr.write("No active university exists. Create one in Campus > Universities first.")
            return

        school, _ = School.objects.get_or_create(university=uni, name="UNIMAP Test School")
        dept, _ = Department.objects.get_or_create(school=school, name="Computer Engineering Test")
        option, _ = Option.objects.get_or_create(department=dept, name="UDT Software Engineering Test", defaults={"code":"UDT-SE-TEST"})
        year, _ = AcademicYear.objects.get_or_create(name="2026/2027")
        Semester.objects.get_or_create(academic_year=year, name="semester_1")
        Semester.objects.get_or_create(academic_year=year, name="semester_2")
        building, _ = Building.objects.get_or_create(
            university=uni, name="UNIMAP Test Attendance Building",
            defaults={"category":"Test", "status":"available", "latitude":0.0, "longitude":0.0, "geofence":[]}
        )
        self.stdout.write(self.style.SUCCESS("UNIMAP test data is ready."))
        self.stdout.write(f"University: {uni.name} ({uni.id})")
        self.stdout.write(f"School: {school.name} ({school.id})")
        self.stdout.write(f"Department: {dept.name} ({dept.id})")
        self.stdout.write(f"Option: {option.name} ({option.id})")
        self.stdout.write("Academic year: 2026/2027; semesters 1 and 2")
        self.stdout.write(f"Test attendance building: {building.name} ({building.id})")
        self.stdout.write("Next: add your house/test polygon to this building in the custom admin before testing attendance.")
