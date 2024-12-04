from analytics.models import Campaign
from rest_framework.test import APITestCase
from .factories import AdGroupStatsFactory, CampaignFactory, TokenFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST
from parameterized import parameterized
from urllib.parse import urlencode


class TestCampaignList(APITestCase):
    def setUp(self):
        super().setUp()
        AdGroupStatsFactory.create_batch(10)
        token = TokenFactory()
        self.client.force_authenticate(user=token.user)
        self.url = reverse("campaigns")

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
        response = self.client.post(self.url, data, format="json")
        assert response.status_code == HTTP_200_OK
        assert response.data["name"] == update_name

        target_campaign.refresh_from_db()
        assert target_campaign.name == update_name

    def test_update_not_exist_campaign_name(self):
        target_campaign = Campaign.objects.first()

        update_name = "Updated Name"
        data = {
            "id": 0,
            "name": update_name,
        }
        response = self.client.post(self.url, data, format="json")
        assert response.status_code == HTTP_404_NOT_FOUND

        target_campaign.refresh_from_db()
        assert target_campaign.name != update_name


class TestPerformanceTimeSeries(APITestCase):
    def setUp(self):
        super().setUp()
        self.campaign_1 = CampaignFactory()
        self.campaign_2 = CampaignFactory()
        self.url = reverse("performance-time-series")
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
        param = {"aggregate_by": "day"}
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


class TestPerformance(APITestCase):
    def setUp(self):
        super().setUp()
        AdGroupStatsFactory.create_batch(5)
        token = TokenFactory()
        self.client.force_authenticate(user=token.user)
        self.url = reverse("performances")

    @parameterized.expand(
        [
            ("preceding", "2022-01-01", "2022-01-31"),
            ("previous_month", "2022-01-01", "2022-01-31"),
        ]
    )
    def test_get_performance(self, compare_mode, start_date, end_date):
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
    def test_get_performance_without_mandatory_params(
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
