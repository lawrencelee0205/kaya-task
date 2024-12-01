from django.contrib import admin
from .models import Campaign, AdGroup, AdGroupStats

# Register your models here.
admin.site.register(Campaign)
admin.site.register(AdGroup)
admin.site.register(AdGroupStats)
