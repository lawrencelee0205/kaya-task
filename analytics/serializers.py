# myapp/serializers.py
from rest_framework import serializers
from .models import Campaign


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            "id",
            "name",
            "campaign_type",
            "ad_groups_count",
            "ad_group_names",
            "average_monthly_cost",
            "average_cost_per_conversion",
        ]

    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    campaign_type = serializers.CharField(read_only=True)
    ad_groups_count = serializers.IntegerField(read_only=True)
    ad_group_names = serializers.ListField(
        child=serializers.CharField(), read_only=True
    )
    average_monthly_cost = serializers.FloatField(read_only=True)
    average_cost_per_conversion = serializers.FloatField(read_only=True)
