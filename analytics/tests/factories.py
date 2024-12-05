import factory
from django.contrib.auth.models import User
from factory import fuzzy
from rest_framework.authtoken.models import Token

from analytics.enums import AdGroupDeviceChoices, CampaignTypeChoices
from analytics.models import AdGroup, AdGroupStats, Campaign


class CampaignFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Campaign
        django_get_or_create = ("name", "campaign_type")

    id = factory.Sequence(lambda n: n)
    name = factory.Faker("word")
    campaign_type = fuzzy.FuzzyChoice(CampaignTypeChoices.choices)


class AdGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AdGroup
        django_get_or_create = ("name",)

    id = factory.Sequence(lambda n: n)
    name = fuzzy.FuzzyText(length=50)
    campaign = factory.SubFactory(CampaignFactory)


class AdGroupStatsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AdGroupStats

    date = factory.Faker("date")
    ad_group = factory.SubFactory(AdGroupFactory)
    device = fuzzy.FuzzyChoice(AdGroupDeviceChoices.choices)
    cost = fuzzy.FuzzyFloat(0)
    conversions = fuzzy.FuzzyFloat(0)
    clicks = fuzzy.FuzzyInteger(0)
    impressions = fuzzy.FuzzyInteger(0)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")


class TokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Token

    user = factory.SubFactory(UserFactory)
