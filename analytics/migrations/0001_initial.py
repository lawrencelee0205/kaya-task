# Generated by Django 5.1.3 on 2024-12-01 06:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AdGroupStatsMetricMixin",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("impressions", models.PositiveIntegerField()),
                ("clicks", models.PositiveIntegerField()),
                ("converstions", models.FloatField()),
                ("cost", models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name="Campaign",
            fields=[
                (
                    "id",
                    models.PositiveBigIntegerField(primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=50)),
                (
                    "campaign_type",
                    models.CharField(
                        choices=[
                            ("Search Standard", "Search Standard"),
                            ("Video Responsive", "Video Responsive"),
                        ],
                        max_length=50,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AdGroup",
            fields=[
                (
                    "id",
                    models.PositiveBigIntegerField(primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=50)),
                (
                    "campaign",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="analytics.campaign",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="AdGroupStats",
            fields=[
                (
                    "adgroupstatsmetricmixin_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="analytics.adgroupstatsmetricmixin",
                    ),
                ),
                ("date", models.DateField()),
                (
                    "device",
                    models.CharField(
                        choices=[
                            ("Desktop", "Desktop"),
                            ("Mobile", "Mobile"),
                            ("Tablet", "Tablet"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "ad_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="analytics.adgroup",
                    ),
                ),
            ],
            bases=("analytics.adgroupstatsmetricmixin",),
        ),
    ]