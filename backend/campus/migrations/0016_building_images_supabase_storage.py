from django.db import migrations, models
import unimap_project.storage


class Migration(migrations.Migration):
    dependencies = [("campus", "0015_building_geofence")]

    operations = [
        migrations.AlterField(
            model_name="building",
            name="photo",
            field=models.ImageField(blank=True, null=True, storage=unimap_project.storage.BuildingMediaStorage(), upload_to="buildings/photos/"),
        ),
        migrations.AlterField(
            model_name="building",
            name="icon",
            field=models.ImageField(blank=True, null=True, storage=unimap_project.storage.BuildingMediaStorage(), upload_to="buildings/icons/"),
        ),
    ]
