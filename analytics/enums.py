from django.db import models


class CampaignTypeChoices(models.TextChoices):
    SEARCH_STANDARD = "Search Standard"
    VIDEO_RESPONSIVE = "Video Responsive"


class AdGroupDeviceChoices(models.TextChoices):
    DESKTOP = "Desktop"
    MOBILE = "Mobile"
    TABLET = "Tablet"
