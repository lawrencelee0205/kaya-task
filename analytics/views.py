from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.status import HTTP_400_BAD_REQUEST
from .models import Campaign, AdGroupStats
from .serializers import (
    CampaignSerializer,
    PerformanceTimeSeriesQuerySerializer,
    PerformanceTimeSeriesMetricSerializer,
)
from django.shortcuts import get_object_or_404
from django.db.models.functions import TruncMonth, TruncDay, TruncWeek
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (
    Subquery,
    OuterRef,
    Count,
    FloatField,
    Sum,
    Avg,
    F,
    Case,
    When,
)


@api_view(["GET", "POST"])
def campaigns(request):
    if request.method == "POST":
        campaign = get_object_or_404(Campaign, id=request.data["id"])
        serializer = CampaignSerializer(campaign, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    average_monthly_cost_subquery = (
        AdGroupStats.objects.filter(ad_group__campaign_id=OuterRef("id"))
        .annotate(
            month=TruncMonth("date"),
        )
        .values(
            "month",
        )
        .annotate(average_monthly_cost=Avg("cost"))
        .values("average_monthly_cost")
    )
    average_cost_per_conversion_subquery = (
        AdGroupStats.objects.filter(ad_group__campaign_id=OuterRef("id"))
        .values(
            "ad_group__campaign_id",
        )
        .alias(
            total_cost=Sum("cost"),
            total_conversion=Sum("conversions"),
        )
        .annotate(
            average_cost_per_conversion=Case(
                When(total_conversion=0, then=0),
                default=F("total_cost") / F("total_conversion"),
                output_field=FloatField(),
            )
        )
        .values("average_cost_per_conversion")
    )
    campaigns = Campaign.objects.annotate(
        ad_group_count=Count("adgroup"),
        ad_group_names=ArrayAgg("adgroup__name", distinct=True),
        average_monthly_cost=Subquery(average_monthly_cost_subquery[:1]),
        average_cost_per_conversion=Subquery(average_cost_per_conversion_subquery[:1]),
    ).values(
        "id",
        "name",
        "campaign_type",
        "ad_group_count",
        "ad_group_names",
        "average_monthly_cost",
        "average_cost_per_conversion",
    )
    serializer = CampaignSerializer(campaigns, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def performance_time_series(request):
    serializer = PerformanceTimeSeriesQuerySerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    start_date = serializer.validated_data.get("start_date")
    end_date = serializer.validated_data.get("end_date")
    campaigns = serializer.validated_data.get("campaigns")

    filter_condition = {}
    if start_date:
        filter_condition["date__gte"] = start_date
    if end_date:
        filter_condition["date__lte"] = end_date
    if campaigns:
        filter_condition["ad_group__campaign__id__in"] = campaigns

    time_granularity = serializer.validated_data.get("aggregate_by")
    time_granularity_aggregate = {}
    match time_granularity:
        case "day":
            time_granularity_aggregate["time_granularity"] = TruncDay("date")
        case "week":
            time_granularity_aggregate["time_granularity"] = TruncWeek("date")
        case "month":
            time_granularity_aggregate["time_granularity"] = TruncMonth("date")

    ad_group_stats = (
        AdGroupStats.objects.filter(**filter_condition)
        .annotate(campaign_id=F("ad_group__campaign__id"), **time_granularity_aggregate)
        .values(
            "campaign_id",
            "time_granularity",
        )
        .annotate(
            total_cost=Sum("cost"),
            total_clicks=Sum("clicks"),
            total_conversions=Sum("conversions"),
            average_cost_per_conversion=Case(
                When(total_conversions=0, then=0),
                default=F("total_cost") / F("total_conversions"),
                output_field=FloatField(),
            ),
            average_cost_per_click=Case(
                When(total_clicks=0, then=0),
                default=F("total_cost") / F("total_clicks"),
                output_field=FloatField(),
            ),
            average_click_through_rate=Case(
                When(impressions=0, then=0),
                default=F("clicks") / F("impressions"),
                output_field=FloatField(),
            ),
            average_conversion_rate=Case(
                When(clicks=0, then=0),
                default=F("conversions") / F("clicks"),
                output_field=FloatField(),
            ),
        )
        .values(
            "campaign_id",
            "total_cost",
            "total_clicks",
            "total_conversions",
            "average_cost_per_conversion",
            "average_cost_per_click",
            "average_click_through_rate",
            "average_conversion_rate",
        )
    )

    serializer = PerformanceTimeSeriesMetricSerializer(data=ad_group_stats, many=True)
    serializer.is_valid()
    return Response(serializer.data)
