from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from campus.models import Building, University
from academic.models import CampusActivity, ClassSession, Course


class Command(BaseCommand):
    help = "Create a small UNIMAP academic/activity dataset for local testing."

    def add_arguments(self, parser):
        parser.add_argument("--university", default="", help="University short name, e.g. UBa")

    def handle(self, *args, **options):
        uni_qs = University.objects.filter(active=True)
        short = options["university"]
        if short:
            uni = uni_qs.filter(short_name__iexact=short).first()
        else:
            uni = uni_qs.first()
        if not uni:
            raise CommandError("No active university found. Create one in the admin first.")

        building = uni.buildings.order_by("id").first()
        if not building:
            raise CommandError("Add at least one building for this university before seeding academic data.")

        course, _ = Course.objects.get_or_create(
            university=uni, code="CSC 308", defaults={"name": "Data Structures"}
        )
        now = timezone.localtime()
        start = (now - timedelta(minutes=5)).time().replace(second=0, microsecond=0)
        end = (now + timedelta(minutes=90)).time().replace(second=0, microsecond=0)
        ClassSession.objects.get_or_create(
            course=course,
            building=building,
            day_of_week=now.weekday(),
            start_time=start,
            end_time=end,
            defaults={"room": building.name, "active": True},
        )
        CampusActivity.objects.get_or_create(
            university=uni,
            title="CSC 308 is ongoing",
            defaults={
                "description": f"{building.name} · Tap to view",
                "activity_type": "event",
                "building": building,
                "start_at": timezone.now() - timedelta(minutes=5),
                "end_at": timezone.now() + timedelta(minutes=90),
                "active": True,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"Seeded academic/activity demo data for {uni.short_name}."))
