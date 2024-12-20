# Generated by Django 5.1.3 on 2024-12-04 10:35

import django.contrib.postgres.indexes
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analytics", "0002_alter_adgroupstats_device_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="adgroup",
            index=django.contrib.postgres.indexes.BTreeIndex(
                fields=["id"], name="ad_group_id_unique"
            ),
        ),
        migrations.AddIndex(
            model_name="adgroupstats",
            index=django.contrib.postgres.indexes.BTreeIndex(
                fields=["date"], name="ad_group_date"
            ),
        ),
        migrations.AddIndex(
            model_name="campaign",
            index=django.contrib.postgres.indexes.BTreeIndex(
                fields=["id"], name="campaign_id_unique"
            ),
        ),
        migrations.AddConstraint(
            model_name="adgroupstats",
            constraint=models.UniqueConstraint(
                fields=("date", "ad_group_id", "device"),
                name="ad_group_date_device_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="campaign",
            constraint=models.UniqueConstraint(
                fields=("name", "campaign_type"), name="campaign_name_type_unique"
            ),
        ),
    ]
