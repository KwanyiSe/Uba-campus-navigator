from django.db import migrations, models


def populate_missing_levels(apps, schema_editor):
    ClassSession = apps.get_model("academic", "ClassSession")
    ClassSession.objects.filter(level__isnull=True).update(level=100)


class Migration(migrations.Migration):
    dependencies = [
        ("academic", "0004_cc_multiple_cohorts"),
    ]

    operations = [
        migrations.RunPython(populate_missing_levels, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="classsession",
            name="level",
            field=models.IntegerField(),
        ),
    ]
