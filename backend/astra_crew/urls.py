from django.urls import path

from .views import (
    AstronautListCreateView,
    AstronautDetailView,
)

urlpatterns = [
    path(
        "astronauts/",
        AstronautListCreateView.as_view(),
        name="astronaut-list-create"
    ),

    path(
        "astronauts/<int:pk>/",
        AstronautDetailView.as_view(),
        name="astronaut-detail"
    ),
]
