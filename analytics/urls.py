from django.urls import path
from analytics import views

urlpatterns = [
    path("v1/campaigns/", views.campaigns, name="campaigns"),
]
