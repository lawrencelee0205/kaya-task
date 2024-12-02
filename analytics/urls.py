from django.urls import path
from analytics import views

urlpatterns = [
    path("v1/campaigns/", views.campaign_list, name="campaign_list"),
]
