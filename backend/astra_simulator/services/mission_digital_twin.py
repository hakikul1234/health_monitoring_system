from django.db.models import Avg, Count, Max, Q

from astra_health.models import VitalSignReading
from astra_alerts.models import HealthAlert
from astra_simulator.models import HabitatTelemetry
from astra_simulator.services.mission_explainability import (
    get_mission_explainability,
)


LATEST_LIMIT = 5

QUALITY_VALUES = ("VALID", "SUSPECT", "UNGRADABLE")


def _iso(value):
    return value.isoformat() if value else None


def _quality_counts(aggregate):
    return {
        quality: aggregate.get(quality.lower(), 0)
        for quality in QUALITY_VALUES
    }


def get_mission_digital_twin_summary(mission):
    """
    Build a read-only mission snapshot from existing records.

    UNGRADABLE measurements are counted but never averaged.
    HealthAlert records remain linked to crew health readings.
    """

    health_queryset = (
        VitalSignReading.objects
        .filter(mission_id=mission.pk)
        .select_related("astronaut", "astronaut__profile")
    )

    health_aggregate = health_queryset.aggregate(
        total=Count("id"),
        latest=Max("recorded_at"),
        valid=Count("id", filter=Q(data_quality="VALID")),
        suspect=Count("id", filter=Q(data_quality="SUSPECT")),
        ungradable=Count("id", filter=Q(data_quality="UNGRADABLE")),
        synthetic=Count("id", filter=Q(is_synthetic=True)),
    )

    latest_health = health_queryset.order_by(
        "-recorded_at", "-id"
    )[:LATEST_LIMIT]

    health_readings = [
        {
            "id": reading.id,
            "astronaut_id": reading.astronaut_id,
            "astronaut_name": reading.astronaut.profile.full_name,
            "astronaut_code": reading.astronaut.astronaut_code,
            "heart_rate_bpm": reading.heart_rate_bpm,
            "spo2_percent": reading.spo2_percent,
            "body_temperature_c": float(reading.body_temperature_c),
            "respiratory_rate_bpm": reading.respiratory_rate_bpm,
            "data_quality": reading.data_quality,
            "recorded_at": _iso(reading.recorded_at),
            "is_synthetic": reading.is_synthetic,
        }
        for reading in latest_health
    ]

    habitat_queryset = HabitatTelemetry.objects.filter(
        mission_id=mission.pk
    )

    habitat_aggregate = habitat_queryset.aggregate(
        total=Count("id"),
        latest=Max("recorded_at"),
        valid=Count("id", filter=Q(data_quality="VALID")),
        suspect=Count("id", filter=Q(data_quality="SUSPECT")),
        ungradable=Count("id", filter=Q(data_quality="UNGRADABLE")),
        synthetic=Count("id", filter=Q(is_synthetic=True)),
        average_oxygen=Avg(
            "oxygen_partial_pressure_kpa",
            filter=~Q(data_quality="UNGRADABLE"),
        ),
        average_co2=Avg(
            "carbon_dioxide_ppm",
            filter=~Q(data_quality="UNGRADABLE"),
        ),
        average_pressure=Avg(
            "cabin_pressure_kpa",
            filter=~Q(data_quality="UNGRADABLE"),
        ),
        average_temperature=Avg(
            "cabin_temperature_c",
            filter=~Q(data_quality="UNGRADABLE"),
        ),
        average_humidity=Avg(
            "relative_humidity_percent",
            filter=~Q(data_quality="UNGRADABLE"),
        ),
    )

    latest_habitat = habitat_queryset.order_by(
        "-recorded_at", "-id"
    )[:LATEST_LIMIT]

    habitat_readings = [
        {
            "id": reading.id,
            "sensor_id": reading.sensor_id,
            "oxygen_partial_pressure_kpa": float(
                reading.oxygen_partial_pressure_kpa
            ),
            "carbon_dioxide_ppm": reading.carbon_dioxide_ppm,
            "cabin_pressure_kpa": float(reading.cabin_pressure_kpa),
            "cabin_temperature_c": float(reading.cabin_temperature_c),
            "relative_humidity_percent": float(
                reading.relative_humidity_percent
            ),
            "scenario": reading.scenario,
            "data_quality": reading.data_quality,
            "recorded_at": _iso(reading.recorded_at),
            "is_synthetic": reading.is_synthetic,
        }
        for reading in latest_habitat
    ]

    alert_queryset = (
        HealthAlert.objects
        .filter(reading__mission_id=mission.pk)
        .select_related(
            "reading",
            "reading__astronaut",
            "reading__astronaut__profile",
        )
    )

    alert_aggregate = alert_queryset.aggregate(
        total=Count("id"),
        open=Count("id", filter=Q(status="OPEN")),
        critical_open=Count(
            "id",
            filter=Q(status="OPEN", severity="CRITICAL"),
        ),
        synthetic=Count("id", filter=Q(is_synthetic=True)),
    )

    latest_alerts = alert_queryset.order_by(
        "-created_at", "-id"
    )[:LATEST_LIMIT]

    alert_data = [
        {
            "id": alert.id,
            "reading_id": alert.reading_id,
            "astronaut_name": (
                alert.reading.astronaut.profile.full_name
            ),
            "severity": alert.severity,
            "parameter": alert.parameter,
            "rule_code": alert.rule_code,
            "observed_value": float(alert.observed_value),
            "explanation": alert.explanation,
            "status": alert.status,
            "is_synthetic": alert.is_synthetic,
            "created_at": _iso(alert.created_at),
        }
        for alert in latest_alerts
    ]

    explainable_intelligence = get_mission_explainability(mission)

    total_records = (
        health_aggregate["total"]
        + habitat_aggregate["total"]
        + alert_aggregate["total"]
    )

    synthetic_records = (
        health_aggregate["synthetic"]
        + habitat_aggregate["synthetic"]
        + alert_aggregate["synthetic"]
    )

    return {
        "mission": {
            "id": mission.id,
            "mission_code": mission.mission_code,
            "mission_name": mission.mission_name,
            "mission_type": mission.mission_type,
            "status": mission.status,
            "destination": mission.destination,
            "crew_count": mission.crew.count(),
        },
        "crew_health": {
            "total_readings": health_aggregate["total"],
            "latest_reading_at": _iso(health_aggregate["latest"]),
            "data_quality_counts": _quality_counts(health_aggregate),
            "latest_readings": health_readings,
        },
        "habitat": {
            "total_readings": habitat_aggregate["total"],
            "latest_reading_at": _iso(habitat_aggregate["latest"]),
            "data_quality_counts": _quality_counts(habitat_aggregate),
            "averages": {
                "oxygen_partial_pressure_kpa": (
                    float(habitat_aggregate["average_oxygen"])
                    if habitat_aggregate["average_oxygen"] is not None
                    else None
                ),
                "carbon_dioxide_ppm": (
                    float(habitat_aggregate["average_co2"])
                    if habitat_aggregate["average_co2"] is not None
                    else None
                ),
                "cabin_pressure_kpa": (
                    float(habitat_aggregate["average_pressure"])
                    if habitat_aggregate["average_pressure"] is not None
                    else None
                ),
                "cabin_temperature_c": (
                    float(habitat_aggregate["average_temperature"])
                    if habitat_aggregate["average_temperature"] is not None
                    else None
                ),
                "relative_humidity_percent": (
                    float(habitat_aggregate["average_humidity"])
                    if habitat_aggregate["average_humidity"] is not None
                    else None
                ),
            },
            "latest_readings": habitat_readings,
        },
        "health_alerts": {
            "total": alert_aggregate["total"],
            "open": alert_aggregate["open"],
            "critical_open": alert_aggregate["critical_open"],
            "latest": alert_data,
        },
        "explainable_intelligence": explainable_intelligence,
        "data_provenance": {
            "total_records": total_records,
            "synthetic_records": synthetic_records,
            "non_synthetic_records": total_records - synthetic_records,
            "all_synthetic": (
                synthetic_records == total_records
                if total_records
                else None
            ),
        },
        "disclaimer": (
            "Research software demonstration using stored mission records. "
            "This summary is not a real-time spacecraft safety assessment, "
            "medical diagnosis, or validated operational decision system. "
            "UNGRADABLE readings are excluded from environmental averages."
        ),
    }
