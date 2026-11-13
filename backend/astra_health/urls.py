from django.urls import path

from .views import (
    HealthReadingListCreateView,
    HealthReadingDetailView,
    HealthReadingAnalysisView,
)

urlpatterns = [

    path(
        "readings/",
        HealthReadingListCreateView.as_view(),
        name="health-reading-list-create"
    ),

    path(
        "readings/<int:pk>/",
        HealthReadingDetailView.as_view(),
        name="health-reading-detail"
    ),

    path(
        "readings/<int:pk>/analysis/",
        HealthReadingAnalysisView.as_view(),
        name="health-reading-analysis"
    ),

]
