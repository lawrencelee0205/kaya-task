# Generated by Django 5.1.3 on 2024-12-04 10:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analytics", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="adgroupstats",
            name="device",
            field=models.CharField(
                choices=[
                    ("DESKTOP", "Desktop"),
                    ("MOBILE", "Mobile"),
                    ("TABLET", "Tablet"),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="campaign",
            name="campaign_type",
            field=models.CharField(
                choices=[
                    ("SEARCH_STANDARD", "Search Standard"),
                    ("VIDEO_RESPONSIVE", "Video Responsive"),
                ],
                max_length=50,
            ),
        ),
    ]
