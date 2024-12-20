from django.urls import path

from analytics import views

urlpatterns = [
    path("api/v1/campaigns/", views.CampaignsListCreate.as_view(), name="campaigns"),
    path(
        "api/v1/performance-time-series/",
        views.PerformanceTimeSeriesList.as_view(),
        name="performance-time-series",
    ),
    path(
        "api/v1/performance-comparison/",
        views.PerformanceComparisonRetrieve.as_view(),
        name="performance-comparison",
    ),
    path("api/v1/register/", views.RegisterView.as_view(), name="register"),
    path("api/v1/login/", views.LoginView.as_view(), name="login"),
]
