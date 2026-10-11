from django.db import migrations, models
import unimap_project.storage


class Migration(migrations.Migration):

    dependencies = [
        ("academic", "0007_merge_20260915_0608"),
    ]

    operations = [
        migrations.AlterField(
            model_name="newsattachment",
            name="file",
            field=models.FileField(
                storage=unimap_project.storage.NewsMediaStorage(),
                upload_to="news/",
            ),
        ),
    ]
