from datetime import timedelta
from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import Campaign, AdGroupStats
from .serializers import (
    CampaignSerializer,
    PerformanceMetricSerializer,
    PerformanceTimeSeriesQuerySerializer,
    PerformanceQuerySerializer,
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


@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
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
    paginator = LimitOffsetPagination()
    page = paginator.paginate_queryset(campaigns, request)

    if page is not None:
        serializer = CampaignSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    serializer = CampaignSerializer(campaigns, many=True)
    return Response(serializer.data)


@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@api_view(["GET"])
def performance_time_series(request):
    data = request.query_params.dict().copy()
    if "campaigns" in data:
        data["campaigns"] = data["campaigns"].split(",")

    serializer = PerformanceTimeSeriesQuerySerializer(data=data)
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
    paginator = LimitOffsetPagination()
    page = paginator.paginate_queryset(ad_group_stats, request)

    if page is not None:
        serializer = PerformanceTimeSeriesMetricSerializer(data=page, many=True)
        serializer.is_valid()
        return paginator.get_paginated_response(data=serializer.data)

    serializer = PerformanceTimeSeriesMetricSerializer(data=ad_group_stats, many=True)
    serializer.is_valid()
    return Response(serializer.data)


@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@api_view(["GET"])
def performances(request):
    serializer = PerformanceQuerySerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

    start_date = serializer.validated_data.get("start_date")
    end_date = serializer.validated_data.get("end_date")
    compare_mode = serializer.validated_data.get("compare_mode")
    date_delta = end_date - start_date

    if compare_mode == "preceding":
        compared_end_date = start_date - timedelta(days=1)
        compared_start_date = compared_end_date - timedelta(days=date_delta.days)
    elif compare_mode == "previous_month":
        compared_end_date = end_date - timedelta(months=1)
        compared_start_date = start_date - timedelta(months=1)

    base_performance = AdGroupStats.objects.filter(
        date__range=(start_date, end_date)
    ).aggregate(
        base_total_cost=Sum("cost"),
        base_total_clicks=Sum("clicks"),
        base_total_conversions=Sum("conversions"),
        base_total_impressions=Sum("impressions"),
        base_cost_per_conversion=Case(
            When(base_total_conversions=0, then=0),
            default=F("base_total_cost") / F("base_total_conversions"),
            output_field=FloatField(),
        ),
        base_cost_per_click=Case(
            When(base_total_clicks=0, then=0),
            default=F("base_total_cost") / F("base_total_clicks"),
            output_field=FloatField(),
        ),
        base_cost_per_mile_impression=Case(
            When(base_total_impressions=0, then=0),
            default=F("base_total_cost") / F("base_total_impressions") * 1000,
            output_field=FloatField(),
        ),
        base_conversion_rate=Case(
            When(base_total_clicks=0, then=0),
            default=F("base_total_conversions") / F("base_total_clicks"),
            output_field=FloatField(),
        ),
        base_click_through_rate=Case(
            When(base_total_impressions=0, then=0),
            default=F("base_total_clicks") / F("base_total_impressions"),
            output_field=FloatField(),
        ),
    )

    compared_performance = AdGroupStats.objects.filter(
        date__range=(compared_start_date, compared_end_date)
    ).aggregate(
        compared_total_cost=Sum("cost"),
        compared_total_clicks=Sum("clicks"),
        compared_total_conversions=Sum("conversions"),
        compared_total_impressions=Sum("impressions"),
        compared_cost_per_conversion=Case(
            When(compared_total_conversions=0, then=0),
            default=F("compared_total_cost") / F("compared_total_conversions"),
            output_field=FloatField(),
        ),
        compared_cost_per_click=Case(
            When(compared_total_clicks=0, then=0),
            default=F("compared_total_cost") / F("compared_total_clicks"),
            output_field=FloatField(),
        ),
        compared_cost_per_mile_impression=Case(
            When(compared_total_impressions=0, then=0),
            default=F("compared_total_cost") / F("compared_total_impressions") * 1000,
            output_field=FloatField(),
        ),
        compared_conversion_rate=Case(
            When(compared_total_clicks=0, then=0),
            default=F("compared_total_conversions") / F("compared_total_clicks"),
            output_field=FloatField(),
        ),
        compared_click_through_rate=Case(
            When(compared_total_impressions=0, then=0),
            default=F("compared_total_clicks") / F("compared_total_impressions"),
            output_field=FloatField(),
        ),
    )

    base_performance.pop("base_total_impressions")
    compared_performance.pop("compared_total_impressions")
    serializer = PerformanceMetricSerializer(
        data={**base_performance, **compared_performance}
    )
    serializer.is_valid()

    return Response(serializer.data)
