from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies=[("campus","0014_building_capacity_building_floor_and_more")]
    operations=[migrations.AddField(model_name="building",name="geofence",field=models.JSONField(blank=True,default=list))]
