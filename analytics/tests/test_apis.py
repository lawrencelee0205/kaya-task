from unittest.mock import patch
from urllib.parse import urlencode

from django.conf import settings
from django.urls import reverse
from parameterized import parameterized
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_429_TOO_MANY_REQUESTS,
)
from rest_framework.test import APITestCase

from analytics.models import Campaign

from .factories import AdGroupStatsFactory, CampaignFactory, TokenFactory


class CampaignListAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        AdGroupStatsFactory.create_batch(30)
        token = TokenFactory()
        self.client.force_authenticate(user=token.user)
        self.url = reverse("campaigns")
        self.throttle_rate = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user"]

    def test_get_campaign_list(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTP_200_OK
        assert len(response.data.get("results")) == 10

    def test_update_campaign_name(self):
        target_campaign = Campaign.objects.first()

        update_name = "Updated Name"
        data = {
            "id": target_campaign.id,
            "name": update_name,
        }
        response = self.client.patch(self.url, data, format="json")
        assert response.status_code == HTTP_200_OK
        assert response.data["name"] == update_name

        target_campaign.refresh_from_db()
        assert target_campaign.name == update_name

    def test_update_not_exist_campaign_name(self):
        target_campaign = Campaign.objects.last()

        update_name = "Updated Name"
        data = {
            "id": target_campaign.id + 1,
            "name": update_name,
        }
        response = self.client.patch(self.url, data, format="json")
        assert response.status_code == HTTP_404_NOT_FOUND

        target_campaign.refresh_from_db()
        assert target_campaign.name != update_name

    @patch("rest_framework.throttling.UserRateThrottle.get_rate")
    def test_get_campaign_list_exceed_throttle_limit(self, mock_get_rate):
        mock_get_rate.return_value = self.throttle_rate
        for _ in range(5):
            response = self.client.get(self.url)
            assert response.status_code == HTTP_200_OK

        response = self.client.get(self.url)
        assert response.status_code == HTTP_429_TOO_MANY_REQUESTS

    @patch("rest_framework.throttling.UserRateThrottle.get_rate")
    def test_update_campaign_name_exceed_throttle_limit(self, mock_get_rate):
        mock_get_rate.return_value = self.throttle_rate
        target_campaign = Campaign.objects.first()

        update_name = "Updated Name"
        data = {
            "id": target_campaign.id,
            "name": update_name,
        }
        for _ in range(5):
            response = self.client.patch(self.url, data, format="json")
            assert response.status_code == HTTP_200_OK

        response = self.client.patch(self.url, data, format="json")
        assert response.status_code == HTTP_429_TOO_MANY_REQUESTS


class PerformanceTimeSeriesAPITestCase(APITestCase):
    """
    expected_results is a list of
    [total_cost, total_conversions, total_clicks, total_impressions, cost, conversions, clicks]
    E.g. [[100, 1, 1, 1, 100, 1, 1],...]
    """

    def setUp(self):
        super().setUp()
        self.campaign_1 = CampaignFactory()
        self.campaign_2 = CampaignFactory()
        self.url = reverse("performance-time-series")
        self.throttle_rate = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user"]
        ad_group_stats_data = [
            {
                "date": "2024-11-27",
                "cost": 100,
                "ad_group__campaign_id": self.campaign_1.id,
                "conversions": 1,
                "clicks": 1,
                "impressions": 1,
            },
            {
                "date": "2024-12-02",
                "cost": 100,
                "ad_group__campaign_id": self.campaign_1.id,
                "conversions": 1,
                "clicks": 1,
                "impressions": 1,
            },
            {
                "date": "2024-12-04",
                "cost": 100,
                "ad_group__campaign_id": self.campaign_1.id,
                "conversions": 1,
                "clicks": 1,
                "impressions": 1,
            },
            {
                "date": "2024-11-27",
                "cost": 100,
                "ad_group__campaign_id": self.campaign_2.id,
                "conversions": 1,
                "clicks": 1,
                "impressions": 1,
            },
            {
                "date": "2024-12-02",
                "cost": 100,
                "ad_group__campaign_id": self.campaign_2.id,
                "conversions": 1,
                "clicks": 1,
                "impressions": 1,
            },
            {
                "date": "2024-12-04",
                "cost": 100,
                "ad_group__campaign_id": self.campaign_2.id,
                "conversions": 1,
                "clicks": 1,
                "impressions": 1,
            },
        ]
        [AdGroupStatsFactory(**data) for data in ad_group_stats_data]
        token = TokenFactory()
        self.client.force_authenticate(user=token.user)

    @parameterized.expand(
        [("day"), ("week"), ("month")],
    )
    def test_get_performance_time_series_with_aggregate_by(self, aggregate_by):
        param = {"aggregate_by": aggregate_by}
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_200_OK

    @parameterized.expand(
        [
            (""),
            ("c1"),
            ("c2"),
            ("c1, c2"),
        ],
    )
    def test_get_performance_time_series_with_campaigns(self, campaigns):
        param = {"aggregate_by": "day"}
        if campaigns != "":
            param["campaigns"] = []
        if "c1" in campaigns:
            param["campaigns"].append(str(self.campaign_1.id))
        if "c2" in campaigns:
            param["campaigns"].append(str(self.campaign_2.id))
        if "campaigns" in param:
            param["campaigns"] = ",".join(param["campaigns"])

        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_200_OK

    @parameterized.expand(
        [
            (None, None),
            ("2024-11-27", None),
            (None, "2024-12-04"),
            ("2024-11-27", "2024-12-04"),
        ],
    )
    def test_get_performance_time_series_with_dates(self, start_date, end_date):
        param = {"aggregate_by": "day"}
        if start_date:
            param["start_date"] = start_date
        if end_date:
            param["end_date"] = end_date

        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_200_OK

    @parameterized.expand(
        [
            (
                "",
                None,
                None,
                [
                    [200, 2, 2, 100, 100, 1, 1],
                    [200, 2, 2, 100, 100, 1, 1],
                    [200, 2, 2, 100, 100, 1, 1],
                ],
            ),
            (
                "",
                "2024-12-02",
                None,
                [
                    [200, 2, 2, 100, 100, 1, 1],
                    [200, 2, 2, 100, 100, 1, 1],
                    [200, 2, 2, 100, 100, 1, 1],
                ],
            ),
            (
                "",
                None,
                "2024-12-02",
                [[200, 2, 2, 100, 100, 1, 1], [200, 2, 2, 100, 100, 1, 1]],
            ),
            (
                "",
                "2024-11-27",
                "2024-12-03",
                [[200, 2, 2, 100, 100, 1, 1], [200, 2, 2, 100, 100, 1, 1]],
            ),
            (
                "c1",
                "2024-11-27",
                "2024-12-04",
                [
                    [100, 1, 1, 100, 100, 1, 1],
                    [100, 1, 1, 100, 100, 1, 1],
                    [100, 1, 1, 100, 100, 1, 1],
                ],
            ),
            (
                "c2",
                "2024-11-27",
                "2024-12-04",
                [
                    [100, 1, 1, 100, 100, 1, 1],
                    [100, 1, 1, 100, 100, 1, 1],
                    [100, 1, 1, 100, 100, 1, 1],
                ],
            ),
            (
                "c1, c2",
                "2024-11-27",
                "2024-12-04",
                [
                    [200, 2, 2, 100, 100, 1, 1],
                    [200, 2, 2, 100, 100, 1, 1],
                    [200, 2, 2, 100, 100, 1, 1],
                ],
            ),
        ]
    )
    def test_get_performance_time_series_data_aggregate_by_day(
        self, campaigns, start_date, end_date, expected_results
    ):
        param = {"aggregate_by": "day"}
        if campaigns != "":
            param["campaigns"] = []
        if "c1" in campaigns:
            param["campaigns"].append(str(self.campaign_1.id))
        if "c2" in campaigns:
            param["campaigns"].append(str(self.campaign_2.id))
        if "campaigns" in param:
            param["campaigns"] = ",".join(param["campaigns"])

        if start_date:
            param["start_date"] = start_date
        if end_date:
            param["end_date"] = end_date

        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_200_OK
        results = response.data.get("results")
        results = [result.values() for result in results]
        zipped_results = [list(zip(a, b)) for a, b in zip(results, expected_results)][0]
        for response_metric, expected_metric in zipped_results:
            assert response_metric == expected_metric

    @parameterized.expand(
        [
            (
                "",
                None,
                None,
                [[200, 2, 2, 100, 100, 1, 1], [400, 4, 4, 100, 100, 1, 1]],
            ),
            (
                "",
                "2024-11-27",
                None,
                [[200, 2, 2, 100, 100, 1, 1], [400, 4, 4, 100, 100, 1, 1]],
            ),
            (
                "",
                None,
                "2024-12-04",
                [[200, 2, 2, 100, 100, 1, 1], [400, 4, 4, 100, 100, 1, 1]],
            ),
            (
                "",
                "2024-11-27",
                "2024-12-04",
                [[200, 2, 2, 100, 100, 1, 1], [400, 4, 4, 100, 100, 1, 1]],
            ),
            (
                "c1",
                "2024-11-27",
                "2024-12-04",
                [[100, 1, 1, 100, 100, 1, 1], [200, 2, 2, 100, 100, 1, 1]],
            ),
            (
                "c2",
                "2024-11-27",
                "2024-12-04",
                [[100, 1, 1, 100, 100, 1, 1], [200, 2, 2, 100, 100, 1, 1]],
            ),
            (
                "c1, c2",
                "2024-11-27",
                "2024-12-04",
                [[200, 2, 2, 100, 100, 1, 1], [400, 4, 4, 100, 100, 1, 1]],
            ),
        ]
    )
    def test_get_performance_time_series_data_aggregate_by_week(
        self,
        campaigns,
        start_date,
        end_date,
        expected_results,
    ):
        param = {"aggregate_by": "week"}
        if campaigns != "":
            param["campaigns"] = []
        if "c1" in campaigns:
            param["campaigns"].append(str(self.campaign_1.id))
        if "c2" in campaigns:
            param["campaigns"].append(str(self.campaign_2.id))
        if "campaigns" in param:
            param["campaigns"] = ",".join(param["campaigns"])

        if start_date:
            param["start_date"] = start_date
        if end_date:
            param["end_date"] = end_date

        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_200_OK
        results = response.data.get("results")
        results = [result.values() for result in results]
        zipped_results = [list(zip(a, b)) for a, b in zip(results, expected_results)][0]
        for response_metric, expected_metric in zipped_results:
            assert response_metric == expected_metric

    @parameterized.expand(
        [
            (
                "",
                None,
                None,
                [[200, 2, 2, 100, 100, 1, 1], [400, 4, 4, 100, 100, 1, 1]],
            ),
            (
                "",
                "2024-11-27",
                None,
                [[200, 2, 2, 100, 100, 1, 1], [400, 4, 4, 100, 100, 1, 1]],
            ),
            (
                "",
                None,
                "2024-12-04",
                [[200, 2, 2, 100, 100, 1, 1], [400, 4, 4, 100, 100, 1, 1]],
            ),
            (
                "",
                "2024-11-27",
                "2024-12-04",
                [[200, 2, 2, 100, 100, 1, 1], [400, 4, 4, 100, 100, 1, 1]],
            ),
            (
                "c1",
                "2024-11-27",
                "2024-12-04",
                [[100, 1, 1, 100, 100, 1, 1], [200, 2, 2, 100, 100, 1, 1]],
            ),
            (
                "c2",
                "2024-11-27",
                "2024-12-04",
                [[100, 1, 1, 100, 100, 1, 1], [200, 2, 2, 100, 100, 1, 1]],
            ),
            (
                "c1, c2",
                "2024-11-27",
                "2024-12-04",
                [[200, 2, 2, 100, 100, 1, 1], [400, 4, 4, 100, 100, 1, 1]],
            ),
        ]
    )
    def test_get_performance_time_series_data_aggregate_by_month(
        self,
        campaigns,
        start_date,
        end_date,
        expected_results,
    ):
        param = {"aggregate_by": "month"}
        if campaigns != "":
            param["campaigns"] = []
        if "c1" in campaigns:
            param["campaigns"].append(str(self.campaign_1.id))
        if "c2" in campaigns:
            param["campaigns"].append(str(self.campaign_2.id))
        if "campaigns" in param:
            param["campaigns"] = ",".join(param["campaigns"])

        if start_date:
            param["start_date"] = start_date
        if end_date:
            param["end_date"] = end_date

        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_200_OK
        results = response.data.get("results")
        results = [result.values() for result in results]
        zipped_results = [list(zip(a, b)) for a, b in zip(results, expected_results)][0]
        for response_metric, expected_metric in zipped_results:
            assert response_metric == expected_metric

    def test_get_performance_time_series_without_aggregate_by(self):
        response = self.client.get(self.url)
        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_get_performance_time_series_without_auth(self):
        self.client.force_authenticate(user=None)
        param = {"aggregate_by": "day"}
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_401_UNAUTHORIZED

    def test_get_performance_time_series_with_invalid_aggregate_by(self):
        param = {"aggregate_by": "invalid"}
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_get_performance_time_series_with_invalid_date_format(self):
        param = {"aggregate_by": "day", "start_date": "01-01-2024"}
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_get_performance_time_series_with_end_date_before_start_date(self):
        param = {
            "aggregate_by": "day",
            "start_date": "2024-12-07",
            "end_date": "2024-12-05",
        }
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_400_BAD_REQUEST

    @patch("rest_framework.throttling.UserRateThrottle.get_rate")
    def test_get_performance_time_series_exceed_throttle_limit(self, mock_get_rate):
        mock_get_rate.return_value = self.throttle_rate
        param = {"aggregate_by": "day"}
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        for _ in range(5):
            response = self.client.get(
                url,
            )
            assert response.status_code == HTTP_200_OK

        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_429_TOO_MANY_REQUESTS


class PerformanceComparisonAPITestCase(APITestCase):
    """
    expected_base_performance and expected_performance_comparisons are in the format:
    [
        total_cost, total_clicks, total_conversions, cost_per_conversion,
        cost_per_click, cost_per_mile_impression, conversion_rate, click_through_rate
    ]
    e.g. [400, 4, 4, 100, 100, 100_000, 1, 1]
    """

    def setUp(self):
        super().setUp()
        self.campaign_1 = CampaignFactory()
        self.campaign_2 = CampaignFactory()
        self.throttle_rate = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user"]
        ad_group_stats_data = [
            {
                "date": "2024-11-27",
                "cost": 100,
                "ad_group__campaign_id": self.campaign_1.id,
                "conversions": 1,
                "clicks": 1,
                "impressions": 1,
            },
            {
                "date": "2024-12-02",
                "cost": 100,
                "ad_group__campaign_id": self.campaign_1.id,
                "conversions": 1,
                "clicks": 1,
                "impressions": 1,
            },
            {
                "date": "2024-12-04",
                "cost": 100,
                "ad_group__campaign_id": self.campaign_1.id,
                "conversions": 1,
                "clicks": 1,
                "impressions": 1,
            },
            {
                "date": "2024-11-27",
                "cost": 100,
                "ad_group__campaign_id": self.campaign_2.id,
                "conversions": 1,
                "clicks": 1,
                "impressions": 1,
            },
            {
                "date": "2024-12-02",
                "cost": 100,
                "ad_group__campaign_id": self.campaign_2.id,
                "conversions": 1,
                "clicks": 1,
                "impressions": 1,
            },
            {
                "date": "2024-12-04",
                "cost": 100,
                "ad_group__campaign_id": self.campaign_2.id,
                "conversions": 1,
                "clicks": 1,
                "impressions": 1,
            },
        ]
        [AdGroupStatsFactory(**data) for data in ad_group_stats_data]
        token = TokenFactory()
        self.client.force_authenticate(user=token.user)
        self.url = reverse("performance-comparison")

    @parameterized.expand(
        [
            ("preceding", "2022-01-01", "2022-01-31"),
            ("previous_month", "2022-01-01", "2022-01-31"),
        ]
    )
    def test_get_performance_comparison(self, compare_mode, start_date, end_date):
        param = {
            "compare_mode": compare_mode,
            "start_date": start_date,
            "end_date": end_date,
        }
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_200_OK

    @parameterized.expand(
        [
            (None, "2022-01-01", "2022-01-31"),
            ("preceding", None, "2022-01-31"),
            ("preceding", "2022-01-01", None),
        ]
    )
    def test_get_performance_comparison_without_mandatory_params(
        self, compare_mode, start_date, end_date
    ):
        param = {
            "compare_mode": compare_mode,
            "start_date": start_date,
            "end_date": end_date,
        }
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_400_BAD_REQUEST

    @parameterized.expand(
        [
            (
                "preceding",
                "2024-12-05",
                "2024-12-07",
                [None, None, None, None, None, None, None, None],
                [400, 4, 4, 100, 100, 100_000, 1, 1],
            ),
            (
                "previous_month",
                "2025-01-02",
                "2025-01-04",
                [None, None, None, None, None, None, None, None],
                [400, 4, 4, 100, 100, 100_000, 1, 1],
            ),
            (
                "preceding",
                "2024-12-05",
                "2024-12-20",
                [None, None, None, None, None, None, None, None],
                [600, 6, 6, 100, 100, 100_000, 1, 1],
            ),
            (
                "previous_month",
                "2024-12-01",
                "2024-12-30",
                [400, 4, 4, 100, 100, 100_000, 1, 1],
                [200, 2, 2, 100, 100, 100_000, 1, 1],
            ),
            (
                "preceding",
                "2024-12-03",
                "2024-12-04",
                [200, 2, 2, 100, 100, 100_000, 1, 1],
                [200, 2, 2, 100, 100, 100_000, 1, 1],
            ),
        ]
    )
    def test_get_performance_comparison_data(
        self,
        compare_mode,
        start_date,
        end_date,
        expected_base_performance,
        expected_compared_performance,
    ):
        param = {
            "compare_mode": compare_mode,
            "start_date": start_date,
            "end_date": end_date,
        }
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_200_OK
        results = response.data
        base_performance_keys = [
            key for key in results.keys() if key.startswith("base")
        ]
        compared_performance_keys = [
            key for key in results.keys() if key.startswith("compared")
        ]

        base_performance_result = [results[key] for key in base_performance_keys]
        compared_performance_result = [
            results[key] for key in compared_performance_keys
        ]

        for response_result, expected_result in list(
            zip(base_performance_result, expected_base_performance)
        ):
            assert response_result == expected_result

        for response_result, expected_result in list(
            zip(compared_performance_result, expected_compared_performance)
        ):
            assert response_result == expected_result

    def test_get_performance_comparison_without_auth(self):
        param = {
            "compare_mode": "preceding",
            "start_date": "2024-12-05",
            "end_date": "2024-12-07",
        }
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        self.client.force_authenticate(user=None)
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_401_UNAUTHORIZED

    def test_get_performance_comparison_with_invalid_compare_mode(self):
        param = {
            "compare_mode": "invalid",
            "start_date": "2024-12-05",
            "end_date": "2024-12-07",
        }
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_get_performance_comparison_with_invalid_date_format(self):
        param = {
            "compare_mode": "preceding",
            "start_date": "01-01-2024",
            "end_date": "01-03-2024",
        }
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_get_performance_comparison_with_end_date_before_start_date(self):
        param = {
            "compare_mode": "preceding",
            "start_date": "2024-12-07",
            "end_date": "2024-12-05",
        }
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_400_BAD_REQUEST

    @patch("rest_framework.throttling.UserRateThrottle.get_rate")
    def test_get_performance_comparison_exceed_throttle_limit(self, mock_get_rate):
        mock_get_rate.return_value = self.throttle_rate
        param = {
            "compare_mode": "preceding",
            "start_date": "2024-12-05",
            "end_date": "2024-12-07",
        }
        query_string = urlencode(param)
        url = f"{self.url}?{query_string}" if query_string else self.url
        for _ in range(5):
            response = self.client.get(
                url,
            )
            assert response.status_code == HTTP_200_OK

        response = self.client.get(
            url,
        )
        assert response.status_code == HTTP_429_TOO_MANY_REQUESTS
