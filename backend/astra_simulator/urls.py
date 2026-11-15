from django.urls import path

from .trust_decision_views import TrustDecisionEvaluationView

from .views import (
    TelemetryGenerationView,
    HabitatTelemetryGenerationView,
    MissionDigitalTwinSummaryView,
)

from .virtual_sensor_views import (
    VirtualHealthSensorListCreateView,
    VirtualSensorSimulationView,
    SensorSimulationRunListView,
)


urlpatterns = [
    path(
        "trust-decisions/",
        TrustDecisionEvaluationView.as_view(),
        name="trust-decision-evaluate",
    ),
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
    path(
        "sensors/",
        VirtualHealthSensorListCreateView.as_view(),
        name="virtual-health-sensor-list-create",
    ),
    path(
        "sensors/<int:sensor_id>/simulate/",
        VirtualSensorSimulationView.as_view(),
        name="virtual-health-sensor-simulate",
    ),
    path(
        "sensor-runs/",
        SensorSimulationRunListView.as_view(),
        name="virtual-sensor-run-list",
    ),
]



