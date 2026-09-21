from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("academic","0002_class_management_news_attendance")]
    operations = [
        migrations.RemoveField(model_name="attendancerecord", name="first_check_at"),
        migrations.RemoveField(model_name="attendancerecord", name="final_check_at"),
    ]
