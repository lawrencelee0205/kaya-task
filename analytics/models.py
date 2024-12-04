from django.contrib.postgres.indexes import BTreeIndex
from django.db import models

from .enums import AdGroupDeviceChoices, CampaignTypeChoices


class Campaign(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    campaign_type = models.CharField(max_length=50, choices=CampaignTypeChoices.choices)

    class Meta:
        indexes = [BTreeIndex(fields=["id"], name="campaign_id_unique")]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "campaign_type"], name="campaign_name_type_unique"
            )
        ]


class AdGroup(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    campaign = models.ForeignKey(
        "Campaign", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        indexes = [BTreeIndex(fields=["id"], name="ad_group_id_unique")]


class AdGroupStatsMetricMixin(models.Model):
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    conversions = models.FloatField(default=0)
    cost = models.FloatField(default=0)

    class Meta:
        abstract = True


class AdGroupStats(AdGroupStatsMetricMixin):
    date = models.DateField()
    ad_group = models.ForeignKey("AdGroup", on_delete=models.CASCADE)
    device = models.CharField(max_length=50, choices=AdGroupDeviceChoices.choices)

    class Meta:
        indexes = [BTreeIndex(fields=["date"], name="ad_group_date")]
