# myapp/serializers.py
from django.contrib.auth.models import User
from django.db import transaction
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
    campaigns = serializers.ListField(child=serializers.CharField(), required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    def validate(self, data):
        start_date = data.get("start_date", None)
        end_date = data.get("end_date", None)

        if start_date is None or end_date is None:
            return data

        if start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date.")

        return data


class PerformanceTimeSeriesMetricSerializer(serializers.Serializer):
    campaign_id = serializers.IntegerField(required=False)
    total_cost = serializers.FloatField()
    total_conversions = serializers.FloatField()
    total_clicks = serializers.IntegerField()
    average_cost_per_click = serializers.FloatField()
    average_cost_per_conversion = serializers.FloatField()
    average_click_through_rate = serializers.FloatField()
    average_conversion_rate = serializers.FloatField()


class PerformanceQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    compare_mode = serializers.ChoiceField(
        choices=[("preceding", "preceding"), ("previous_month", "previous_month")]
    )

    def validate(self, data):
        start_date = data.get("start_date", None)
        end_date = data.get("end_date", None)

        if start_date is None or end_date is None:
            return data

        if start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date.")

        return data


class BasePerformanceSerializer(serializers.Serializer):
    base_total_cost = serializers.FloatField()
    base_total_clicks = serializers.IntegerField()
    base_total_conversions = serializers.FloatField()
    base_cost_per_conversion = serializers.FloatField()
    base_cost_per_click = serializers.FloatField()
    base_cost_per_mile_impression = serializers.FloatField()
    base_conversion_rate = serializers.FloatField()
    base_click_through_rate = serializers.FloatField()


class ComparedPerformanceSerializer(serializers.Serializer):
    compared_total_cost = serializers.FloatField()
    compared_total_clicks = serializers.IntegerField()
    compared_total_conversions = serializers.FloatField()
    compared_cost_per_conversion = serializers.FloatField()
    compared_cost_per_click = serializers.FloatField()
    compared_cost_per_mile_impression = serializers.FloatField()
    compared_conversion_rate = serializers.FloatField()
    compared_click_through_rate = serializers.FloatField()


class PerformanceMetricSerializer(
    BasePerformanceSerializer, ComparedPerformanceSerializer
):
    pass


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "password", "email")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
