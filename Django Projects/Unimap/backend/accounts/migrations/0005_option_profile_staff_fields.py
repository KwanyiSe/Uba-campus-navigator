from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


def populate_profiles(apps, schema_editor):
    Profile = apps.get_model("accounts", "Profile")
    User = apps.get_model(settings.AUTH_USER_MODEL)
    for p in Profile.objects.select_related("user").all():
        name = f"{p.user.first_name} {p.user.last_name}".strip() or p.user.username
        p.full_name = name
        p.save(update_fields=["full_name"])


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_school_logo")]
    operations = [
        migrations.AddField(
            model_name="department", name="logo",
            field=models.ImageField(blank=True, null=True, upload_to="departments/logos/")
        ),
        migrations.CreateModel(
            name="Option",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150)),
                ("code", models.CharField(blank=True, max_length=40)),
                ("active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("department", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="options", to="accounts.department")),
            ],
            options={"ordering":["name"]},
        ),
        migrations.AddConstraint(
            model_name="option",
            constraint=models.UniqueConstraint(fields=("department","name"), name="unique_option_per_department"),
        ),
        migrations.AddField(model_name="profile", name="full_name", field=models.CharField(blank=True,max_length=180)),
        migrations.AddField(model_name="profile", name="profile_picture", field=models.ImageField(blank=True,null=True,upload_to="profiles/")),
        migrations.AddField(model_name="profile", name="option", field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="profiles",to="accounts.option")),
        migrations.AlterField(model_name="profile", name="role", field=models.CharField(choices=[("student","Student"),("lecturer","Lecturer"),("cc","Class Coordinator"),("school_admin","School Admin"),("admin","University Admin")],default="student",max_length=20)),
        migrations.RunPython(populate_profiles, migrations.RunPython.noop),
    ]
