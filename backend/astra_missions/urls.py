from django.urls import path

from .views import (
    MissionListCreateView,
    MissionDetailView,
)

from .dashboard_views import DashboardAnalyticsView

urlpatterns = [

    path(
        "dashboard/analytics/",
        DashboardAnalyticsView.as_view(),
        name="dashboard-analytics"
    ),

    path(
        "",
        MissionListCreateView.as_view(),
        name="mission-list-create"
    ),

    path(
        "<int:pk>/",
        MissionDetailView.as_view(),
        name="mission-detail"
    ),

]
