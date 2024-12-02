from rest_framework.test import APITestCase
from .factories import AdGroupStatsFactory
from django.urls import reverse


class TestCampaignList(APITestCase):
    def setUp(self):
        super().setUp()
        AdGroupStatsFactory.create_batch(10)

    def test_campaign_list(self):
        url = reverse("campaign_list")
        response = self.client.get(url)
        assert response.status_code == 200
        assert len(response.data) == 10
