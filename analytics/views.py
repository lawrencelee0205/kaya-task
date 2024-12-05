from dateutil.relativedelta import relativedelta
from django.contrib.auth import authenticate, login
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import (
    Avg,
    Case,
    Count,
    F,
    FloatField,
    OuterRef,
    Subquery,
    Sum,
    When,
)
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from django.shortcuts import get_object_or_404
from knox.auth import TokenAuthentication
from knox.views import LoginView as KnoxLoginView
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from .models import AdGroupStats, Campaign
from .serializers import (
    CampaignSerializer,
    LoginSerializer,
    PerformanceMetricSerializer,
    PerformanceQuerySerializer,
    PerformanceTimeSeriesMetricSerializer,
    PerformanceTimeSeriesQuerySerializer,
    UserSerializer,
)


class CampaignsListCreate(ListAPIView, UpdateAPIView):
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def list(self, request, *args, **kwargs):
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
            average_cost_per_conversion=Subquery(
                average_cost_per_conversion_subquery[:1]
            ),
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
        page = self.paginate_queryset(serializer.data)
        return self.get_paginated_response(page)

    def patch(self, request, *args, **kwargs):
        campaign = get_object_or_404(Campaign, id=request.data["id"])
        serializer = CampaignSerializer(campaign, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PerformanceTimeSeriesList(ListAPIView):
    pagination_class = LimitOffsetPagination
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def list(self, request, *args, **kwargs):
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

        group_by_values = ["time_granularity"]

        final_values = [
            "total_cost",
            "total_clicks",
            "total_conversions",
            "average_cost_per_conversion",
            "average_cost_per_click",
            "average_click_through_rate",
            "average_conversion_rate",
        ]

        ad_group_stats_metric = {
            "total_cost": Sum("cost"),
            "total_clicks": Sum("clicks"),
            "total_conversions": Sum("conversions"),
            "average_cost_per_conversion": Case(
                When(total_conversions=0, then=0),
                default=F("total_cost") / F("total_conversions"),
                output_field=FloatField(),
            ),
            "average_cost_per_click": Case(
                When(total_clicks=0, then=0),
                default=F("total_cost") / F("total_clicks"),
                output_field=FloatField(),
            ),
            "average_click_through_rate": Case(
                When(impressions=0, then=0),
                default=F("clicks") / F("impressions"),
                output_field=FloatField(),
            ),
            "average_conversion_rate": Case(
                When(clicks=0, then=0),
                default=F("conversions") / F("clicks"),
                output_field=FloatField(),
            ),
        }

        ad_group_stats = (
            AdGroupStats.objects.filter(**filter_condition)
            .annotate(
                campaign_id=F("ad_group__campaign__id"), **time_granularity_aggregate
            )
            .values(
                *group_by_values,
            )
            .annotate(**ad_group_stats_metric)
            .order_by("time_granularity")
            .values(*final_values)
        )
        serializer = PerformanceTimeSeriesMetricSerializer(
            data=list(ad_group_stats), many=True
        )

        if serializer.is_valid():
            page = self.paginate_queryset(serializer.data)
            return self.get_paginated_response(page)

        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class PerformanceComparisonRetrieve(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, *args, **kwargs):
        serializer = PerformanceQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)

        start_date = serializer.validated_data.get("start_date")
        end_date = serializer.validated_data.get("end_date")
        compare_mode = serializer.validated_data.get("compare_mode")
        date_delta = end_date - start_date

        if compare_mode == "preceding":
            compared_end_date = start_date - relativedelta(days=1)
            compared_start_date = compared_end_date - relativedelta(
                days=date_delta.days
            )
        elif compare_mode == "previous_month":
            compared_end_date = end_date - relativedelta(months=1)
            compared_start_date = start_date - relativedelta(months=1)

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
                default=F("compared_total_cost")
                / F("compared_total_impressions")
                * 1000,
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

        serializer = PerformanceMetricSerializer(
            data={**base_performance, **compared_performance}
        )
        serializer.is_valid()

        return Response(serializer.data)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"user": serializer.data}, status=201)
        return Response(serializer.errors, status=400)


class LoginView(KnoxLoginView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
        else:
            return Response({"error": "Invalid login credentials"}, status=401)

        return super(LoginView, self).post(request, format=None)
