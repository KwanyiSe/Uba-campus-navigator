from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("campus", "0016_building_images_supabase_storage"),
    ]

    operations = [
        migrations.CreateModel(
            name="DailyVisit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_key", models.CharField(max_length=40)),
                ("date", models.DateField()),
                ("university", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="daily_visit_records", to="campus.university")),
            ],
            options={
                "indexes": [models.Index(fields=["university", "date"], name="campus_daily_univ_d3d1e2_idx")],
                "constraints": [models.UniqueConstraint(fields=("session_key", "university", "date"), name="uniq_daily_browser_visit")],
            },
        ),
    ]
