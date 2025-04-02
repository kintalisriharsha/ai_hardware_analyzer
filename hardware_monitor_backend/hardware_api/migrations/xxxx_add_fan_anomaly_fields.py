# Create a new migration file for adding the fan anomaly fields
# hardware_api/migrations/xxxx_add_fan_anomaly_fields.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hardware_api', '0001_initial'),  # Replace with your last migration
    ]

    operations = [
        migrations.AddField(
            model_name='systemmetric',
            name='fan_anomaly',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='systemmetric',
            name='fan_expected_speed',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='systemmetric',
            name='fan_rpm_min',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='systemmetric',
            name='fan_rpm_max',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]