from analytics.models import Campaign
from rest_framework.test import APITestCase
from .factories import AdGroupStatsFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND


class TestCampaignList(APITestCase):
    def setUp(self):
        super().setUp()
        AdGroupStatsFactory.create_batch(10)

    def test_get_campaign_list(self):
        url = reverse("campaigns")
        response = self.client.get(url)
        assert response.status_code == HTTP_200_OK
        assert len(response.data) == 10

    def test_update_campaign_name(self):
        target_campaign = Campaign.objects.first()

        url = reverse("campaigns")
        update_name = "Updated Name"
        data = {
            "id": target_campaign.id,
            "name": update_name,
        }
        response = self.client.post(url, data, format="json")
        assert response.status_code == HTTP_200_OK
        assert response.data["name"] == update_name

        target_campaign.refresh_from_db()
        assert target_campaign.name == update_name

    def test_update_not_exist_campaign_name(self):
        target_campaign = Campaign.objects.first()

        url = reverse("campaigns")
        update_name = "Updated Name"
        data = {
            "id": 0,
            "name": update_name,
        }
        response = self.client.post(url, data, format="json")
        assert response.status_code == HTTP_404_NOT_FOUND

        target_campaign.refresh_from_db()
        assert target_campaign.name != update_name
