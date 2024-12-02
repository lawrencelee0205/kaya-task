# myapp/serializers.py
from rest_framework import serializers
from .models import Campaign
from django.db import transaction


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
    name = serializers.CharField(read_only=False)
    campaign_type = serializers.CharField(read_only=True)
    ad_groups_count = serializers.IntegerField(read_only=True)
    ad_group_names = serializers.ListField(
        child=serializers.CharField(), read_only=True
    )
    average_monthly_cost = serializers.FloatField(read_only=True)
    average_cost_per_conversion = serializers.FloatField(read_only=True)

    @transaction.atomic
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)


class PerformanceTimeSeriesQuerySerializer(serializers.Serializer):
    aggregate_by = serializers.ChoiceField(
        choices=[("day", "day"), ("week", "week"), ("month", "month")]
    )
    campaigns = serializers.ListField(
        child=serializers.IntegerField(), read_only=True, required=False
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)


class PerformanceTimeSeriesMetricSerializer(serializers.Serializer):
    campaign_id = serializers.IntegerField(read_only=True)
    total_cost = serializers.FloatField(read_only=True)
    total_conversions = serializers.FloatField(read_only=True)
    total_clicks = serializers.IntegerField(read_only=True)
    average_cost_per_click = serializers.FloatField(read_only=True)
    average_cost_per_conversion = serializers.FloatField(read_only=True)
    average_click_through_rate = serializers.FloatField(read_only=True)
    average_conversion_rate = serializers.FloatField(read_only=True)
