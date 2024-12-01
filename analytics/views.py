from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Campaign, AdGroupStats
from .serializers import CampaignSerializer
from django.db.models.functions import TruncMonth
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (
    Subquery,
    OuterRef,
    Count,
    FloatField,
    Sum,
    ExpressionWrapper,
    Avg,
    F,
)


@api_view(["GET"])
def campaign_list(request):
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
            average_cost_per_conversion=ExpressionWrapper(
                F("total_cost") / F("total_conversion"),
                output_field=FloatField(),
            ),
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
