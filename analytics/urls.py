from django.urls import path
from analytics import views

urlpatterns = [
    path("campaigns/", views.campaign_list),
]
