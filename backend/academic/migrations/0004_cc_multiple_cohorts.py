from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("academic","0003_simplify_attendance_checks")]
    operations = [
        migrations.AlterField(
            model_name="classcoordinatorassignment",
            name="coordinator",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="coordinator_assignments",to="accounts.profile"),
        ),
    ]
