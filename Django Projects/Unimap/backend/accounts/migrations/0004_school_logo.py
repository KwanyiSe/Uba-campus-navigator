from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_backfill_missing_profiles"),
    ]

    operations = [
        migrations.AddField(
            model_name="school",
            name="logo",
            field=models.ImageField(blank=True, null=True, upload_to="schools/logos/"),
        ),
    ]
