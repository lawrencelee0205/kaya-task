from django.urls import path
from analytics import views

urlpatterns = [
    path("v1/campaigns/", views.campaigns, name="campaigns"),
    path(
        "v1/performance-time-series/",
        views.performance_time_series,
        name="performance-time-series",
    ),
    path(
        "v1/performance-time-series/",
        views.performance_time_series,
        name="performance-time-series",
    ),
    path("v1/performances/", views.performances, name="performances"),
]
