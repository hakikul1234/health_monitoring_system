from django.urls import path

from .views import (
    TelemetryGenerationView,
    HabitatTelemetryGenerationView,
    MissionDigitalTwinSummaryView,
)


urlpatterns = [
    path(
        "telemetry/generate/",
        TelemetryGenerationView.as_view(),
        name="telemetry-generate",
    ),
    path(
        "habitat/generate/",
        HabitatTelemetryGenerationView.as_view(),
        name="habitat-telemetry-generate",
    ),
    path(
        "missions/<int:mission_id>/digital-twin/",
        MissionDigitalTwinSummaryView.as_view(),
        name="mission-digital-twin-summary",
    ),
]
