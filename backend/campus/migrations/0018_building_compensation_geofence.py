from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("campus", "0017_dailyvisit")]

    operations = [
        migrations.AddField(
            model_name="building",
            name="compensation_geofence",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="building",
            name="geofence_buffer_m",
            field=models.PositiveSmallIntegerField(default=10),
        ),
        migrations.AddField(
            model_name="building",
            name="geofence_status",
            field=models.CharField(
                choices=[("draft", "Draft"), ("approved", "Approved")],
                default="draft",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="building",
            name="geofence_version",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
