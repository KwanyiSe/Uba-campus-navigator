from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
from django.utils import timezone


def migrate_meetings(apps, schema_editor):
    Activity = apps.get_model("academic", "CampusActivity")
    Activity.objects.filter(activity_type="meeting").update(activity_type="event")


class Migration(migrations.Migration):
    dependencies = [("academic","0001_initial"),("accounts","0005_option_profile_staff_fields")]
    operations = [
        migrations.CreateModel(
            name="Timetable",
            fields=[
                ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
                ("level",models.IntegerField()),
                ("title",models.CharField(max_length=160)),
                ("file",models.FileField(upload_to="academic/timetables/")),
                ("uploaded_at",models.DateTimeField(auto_now_add=True)),
                ("active",models.BooleanField(default=True)),
                ("department",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="timetables",to="accounts.department")),
                ("option",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="timetables",to="accounts.option")),
                ("school",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="timetables",to="accounts.school")),
                ("university",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="timetables",to="campus.university")),
                ("uploaded_by",models.ForeignKey(null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="uploaded_timetables",to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering":["-uploaded_at"]},
        ),
        migrations.CreateModel(
            name="ClassCoordinatorAssignment",
            fields=[
                ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
                ("level",models.IntegerField()),
                ("active",models.BooleanField(default=True)),
                ("appointed_at",models.DateTimeField(auto_now_add=True)),
                ("coordinator",models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name="coordinator_assignment",to="accounts.profile")),
                ("option",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="coordinator_assignments",to="accounts.option")),
            ],
            options={"constraints":[models.UniqueConstraint(fields=("option","level"),name="unique_coordinator_per_option_level")]},
        ),
        migrations.AddField(model_name="classsession",name="option",field=models.ForeignKey(null=True,on_delete=django.db.models.deletion.CASCADE,related_name="class_sessions",to="accounts.option")),
        migrations.AddField(model_name="classsession",name="level",field=models.IntegerField(null=True)),
        migrations.AddField(model_name="classsession",name="status",field=models.CharField(choices=[("scheduled","Scheduled"),("active","Active"),("completed","Completed"),("cancelled","Cancelled")],default="scheduled",max_length=20)),
        migrations.AddField(model_name="classsession",name="started_at",field=models.DateTimeField(blank=True,null=True)),
        migrations.AddField(model_name="classsession",name="ended_at",field=models.DateTimeField(blank=True,null=True)),
        migrations.AddField(model_name="classsession",name="lecturer",field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="lecturer_sessions",to="accounts.profile")),
        migrations.AddField(model_name="classsession",name="coordinator",field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.SET_NULL,related_name="coordinator_sessions",to="accounts.profile")),
        migrations.AddField(model_name="classsession",name="created_by",field=models.ForeignKey(blank=True,null=True,on_delete=django.db.models.SET_NULL,related_name="created_class_sessions",to=settings.AUTH_USER_MODEL)),
        migrations.AlterField(model_name="classsession",name="session_date",field=models.DateField(default=timezone.localdate)),
        migrations.AlterField(model_name="attendancerecord",name="status",field=models.CharField(choices=[("present","Present"),("absent","Absent")],default="absent",max_length=12)),
        migrations.AddField(model_name="attendancerecord",name="verification_method",field=models.CharField(choices=[("automatic","Automatic"),("manual","Manual"),("legacy","Legacy")],default="automatic",max_length=20)),
        migrations.CreateModel(
            name="NewsPost",
            fields=[
                ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
                ("post_type",models.CharField(choices=[("study_group","Study Group"),("campus_news","Campus News")],max_length=20)),
                ("title",models.CharField(max_length=180)),
                ("body",models.TextField()),
                ("audience",models.CharField(choices=[("university","Whole University"),("school","School"),("department","Department"),("option","Option"),("level","Level")],default="university",max_length=20)),
                ("level",models.IntegerField(blank=True,null=True)),
                ("created_at",models.DateTimeField(auto_now_add=True)),
                ("updated_at",models.DateTimeField(auto_now=True)),
                ("active",models.BooleanField(default=True)),
                ("author",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="news_posts",to="accounts.profile")),
                ("department",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.CASCADE,related_name="news_posts",to="accounts.department")),
                ("option",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.CASCADE,related_name="news_posts",to="accounts.option")),
                ("school",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.CASCADE,related_name="news_posts",to="accounts.school")),
                ("university",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="news_posts",to="campus.university")),
            ],
            options={"ordering":["-created_at"]},
        ),
        migrations.CreateModel(
            name="NewsAttachment",
            fields=[
                ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
                ("file",models.FileField(upload_to="academic/news/")),
                ("original_name",models.CharField(blank=True,max_length=255)),
                ("uploaded_at",models.DateTimeField(auto_now_add=True)),
                ("post",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="attachments",to="academic.newspost")),
            ],
        ),
        migrations.AlterField(model_name="campusactivity",name="activity_type",field=models.CharField(choices=[("event","Event"),("group","Study Group"),("notice","Notice")],default="event",max_length=20)),
        migrations.RunPython(migrate_meetings,migrations.RunPython.noop),
    ]
