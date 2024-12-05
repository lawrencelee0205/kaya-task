import csv

from analytics.models import AdGroup, AdGroupStats, Campaign

print("Populating Campaigns...")
campaigns = []
with open("campaign.csv", "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        campaigns.append(
            Campaign(
                id=row["campaign_id"],
                name=row["campaign_name"],
                campaign_type=row["campaign_type"],
            )
        )

campaigns = Campaign.objects.bulk_create(campaigns)
print(f"{campaigns} campaigns added.")

print("Populating AdGroups...")
ad_groups = []
with open("ad_group.csv", "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        ad_groups.append(
            AdGroup(
                id=row["ad_group_id"],
                name=row["ad_group_name"],
                campaign_id=row["campaign_id"],
            )
        )

ad_groups = AdGroup.objects.bulk_create(ad_groups)
print(f"{ad_groups} ad groups added.")

print("Populating AdGroupStats...")
ad_group_stats = []
with open("ad_group_stats.csv", "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        ad_group_stats.append(
            AdGroupStats(
                date=row["date"],
                ad_group_id=row["ad_group_id"],
                device=row["device"],
                impressions=row["impressions"],
                clicks=row["clicks"],
                conversions=row["conversions"],
                cost=row["cost"],
            )
        )

ad_group_stats = AdGroupStats.objects.bulk_create(ad_group_stats)
print(f"{ad_group_stats} ad group stats added.")
