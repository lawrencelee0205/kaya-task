from django.db import models
from .enums import CampaignTypeChoices, AdGroupDeviceChoices


class Campaign(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    campaign_type = models.CharField(max_length=50, choices=CampaignTypeChoices.choices)


class AdGroup(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True)
    name = models.CharField(max_length=50)
    campaign = models.ForeignKey(
        "Campaign", on_delete=models.SET_NULL, null=True, blank=True
    )


class AdGroupStatsMetricMixin(models.Model):
    impressions = models.PositiveIntegerField()
    clicks = models.PositiveIntegerField()
    converstions = models.FloatField()
    cost = models.FloatField()


class AdGroupStats(AdGroupStatsMetricMixin):
    date = models.DateField()
    ad_group = models.ForeignKey("AdGroup", on_delete=models.CASCADE)
    device = models.CharField(max_length=50, choices=AdGroupDeviceChoices.choices)
