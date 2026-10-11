from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("accounts", "0008_alter_profile_profile_picture")]
    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("notification_type", models.CharField(choices=[("general", "General"), ("class", "Class"), ("attendance", "Attendance"), ("form_b", "Form B"), ("news", "News"), ("staff", "Staff")], default="general", max_length=20)),
                ("title", models.CharField(max_length=180)),
                ("body", models.TextField(blank=True)),
                ("link", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("recipient", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="accounts.profile")),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
