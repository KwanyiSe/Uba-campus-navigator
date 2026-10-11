from django.db import migrations


def create_missing_profiles(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Profile = apps.get_model("accounts", "Profile")
    University = apps.get_model("campus", "University")

    university = University.objects.filter(active=True).order_by("id").first()
    if not university:
        return

    existing = set(Profile.objects.values_list("user_id", flat=True))
    Profile.objects.bulk_create([
        Profile(user_id=user.id, university_id=university.id, role="student")
        for user in User.objects.all()
        if user.id not in existing
    ])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_department_remove_profile_department_name_and_more"),
    ]

    operations = [
        migrations.RunPython(create_missing_profiles, noop),
    ]
