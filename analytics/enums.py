from django.db import models


class CampaignTypeChoices(models.TextChoices):
    SEARCH_STANDARD = "SEARCH_STANDARD"
    VIDEO_RESPONSIVE = "VIDEO_RESPONSIVE"


class AdGroupDeviceChoices(models.TextChoices):
    DESKTOP = "DESKTOP"
    MOBILE = "MOBILE"
    TABLET = "TABLET"
