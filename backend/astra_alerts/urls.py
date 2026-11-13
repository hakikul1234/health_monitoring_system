from django.urls import path

from .views import (
    HealthAlertListView,
    HealthAlertDetailView,
    HealthAlertStatisticsView,
    HealthAlertAcknowledgeView,
    HealthAlertResolveView,
)

urlpatterns = [

    path(
        "statistics/",
        HealthAlertStatisticsView.as_view(),
        name="alert-statistics"
    ),

    path(
        "",
        HealthAlertListView.as_view(),
        name="alert-list"
    ),

    path(
        "<int:pk>/",
        HealthAlertDetailView.as_view(),
        name="alert-detail"
    ),

    path(
        "<int:pk>/acknowledge/",
        HealthAlertAcknowledgeView.as_view(),
        name="alert-acknowledge"
    ),

    path(
        "<int:pk>/resolve/",
        HealthAlertResolveView.as_view(),
        name="alert-resolve"
    ),
]
