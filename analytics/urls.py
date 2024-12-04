from django.urls import path
from analytics import views

urlpatterns = [
    path("v1/campaigns/", views.CampaignsListCreate.as_view(), name="campaigns"),
    path(
        "v1/performance-time-series/",
        views.PerformanceTimeSeriesList.as_view(),
        name="performance-time-series",
    ),
    path("v1/performances/", views.PerformanceRetrieve.as_view(), name="performances"),
]
