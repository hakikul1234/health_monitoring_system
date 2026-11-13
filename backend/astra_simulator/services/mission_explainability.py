from django.db.models import Count, Q
from django.utils import timezone

from astra_alerts.models import HealthAlert
from astra_simulator.models import HabitatTelemetry
from astra_simulator.services.habitat_simulator import HABITAT_SCENARIOS


FINDINGS_LIMIT = 10

QUALITY_VALUES = ("VALID", "SUSPECT", "UNGRADABLE")


def _iso(value):
    return value.isoformat() if value else None


def _quality_counts(queryset):
    counts = queryset.aggregate(
        valid=Count("id", filter=Q(data_quality="VALID")),
        suspect=Count("id", filter=Q(data_quality="SUSPECT")),
        ungradable=Count("id", filter=Q(data_quality="UNGRADABLE")),
    )

    return {
        quality: counts.get(quality.lower(), 0)
        for quality in QUALITY_VALUES
    }


def get_mission_explainability(mission):
    """
    Build an evidence-linked, read-only explanation of mission records.

    Crew findings use persisted HealthAlert explanations.
    Habitat findings use explicitly labelled synthetic scenario metadata.
    UNGRADABLE habitat measurements are never interpreted.
    This service does not create diagnoses or spacecraft safety decisions.
    """

    alerts = (
        HealthAlert.objects
        .filter(reading__mission_id=mission.pk)
        .select_related(
            "reading",
            "reading__astronaut",
            "reading__astronaut__profile",
        )
        .order_by("-created_at", "-id")
    )

    crew_findings = []

    for alert in alerts[:FINDINGS_LIMIT]:
        astronaut = alert.reading.astronaut
        profile = getattr(astronaut, "profile", None)

        crew_findings.append({
            "source": "CREW_HEALTH_ALERT",
            "source_record_id": alert.id,
            "reading_id": alert.reading_id,
            "astronaut_code": astronaut.astronaut_code,
            "astronaut_name": (
                profile.full_name if profile else None
            ),
            "severity": alert.severity,
            "status": alert.status,
            "parameter": alert.parameter,
            "rule_code": alert.rule_code,
            "observed_value": float(alert.observed_value),
            "explanation": alert.explanation,
            "recorded_at": _iso(alert.reading.recorded_at),
            "created_at": _iso(alert.created_at),
            "is_synthetic": alert.is_synthetic,
            "evidence_type": "PERSISTED_ALERT_EXPLANATION",
        })

    habitat_queryset = HabitatTelemetry.objects.filter(
        mission_id=mission.pk
    )

    habitat_quality = _quality_counts(habitat_queryset)

    usable_habitat = habitat_queryset.exclude(
        data_quality=HabitatTelemetry.DataQuality.UNGRADABLE
    )

    suspect_habitat = (
        usable_habitat
        .filter(data_quality=HabitatTelemetry.DataQuality.SUSPECT)
        .order_by("-recorded_at", "-id")
    )

    habitat_findings = []

    for reading in suspect_habitat[:FINDINGS_LIMIT]:
        scenario_info = HABITAT_SCENARIOS.get(
            reading.scenario,
            {},
        )

        habitat_findings.append({
            "source": "HABITAT_TELEMETRY",
            "source_record_id": reading.id,
            "sensor_id": reading.sensor_id,
            "scenario": reading.scenario,
            "scenario_description": scenario_info.get(
                "description",
                "No scenario description available.",
            ),
            "data_quality": reading.data_quality,
            "observations": {
                "oxygen_partial_pressure_kpa": float(
                    reading.oxygen_partial_pressure_kpa
                ),
                "carbon_dioxide_ppm": reading.carbon_dioxide_ppm,
                "cabin_pressure_kpa": float(
                    reading.cabin_pressure_kpa
                ),
                "cabin_temperature_c": float(
                    reading.cabin_temperature_c
                ),
                "relative_humidity_percent": float(
                    reading.relative_humidity_percent
                ),
            },
            "explanation": (
                "This record belongs to a SUSPECT synthetic habitat "
                "scenario. Its scenario description and measurements "
                "are presented as simulation evidence, not as a "
                "validated spacecraft safety limit."
            ),
            "recorded_at": _iso(reading.recorded_at),
            "is_synthetic": reading.is_synthetic,
            "evidence_type": "SYNTHETIC_SCENARIO_METADATA",
        })

    alert_counts = alerts.aggregate(
        total=Count("id"),
        synthetic=Count("id", filter=Q(is_synthetic=True)),
        non_synthetic=Count("id", filter=Q(is_synthetic=False)),
        open=Count("id", filter=Q(status=HealthAlert.Status.OPEN)),
        critical_open=Count(
            "id",
            filter=Q(
                status=HealthAlert.Status.OPEN,
                severity=HealthAlert.Severity.CRITICAL,
            ),
        ),
        warning_open=Count(
            "id",
            filter=Q(
                status=HealthAlert.Status.OPEN,
                severity=HealthAlert.Severity.WARNING,
            ),
        ),
    )

    habitat_audit_counts = habitat_queryset.aggregate(
        total=Count("id"),
        synthetic=Count("id", filter=Q(is_synthetic=True)),
        non_synthetic=Count("id", filter=Q(is_synthetic=False)),
    )

    total_evidence_records = (
        alert_counts["total"] + habitat_audit_counts["total"]
    )

    synthetic_evidence_records = (
        alert_counts["synthetic"]
        + habitat_audit_counts["synthetic"]
    )

    non_synthetic_evidence_records = (
        alert_counts["non_synthetic"]
        + habitat_audit_counts["non_synthetic"]
    )

    audit_summary = {
        "audit_generated_at": timezone.now().isoformat(),
        "record_scope": (
            "Unique source records from HealthAlert and HabitatTelemetry. "
            "Linked VitalSignReading references are not counted separately."
        ),
        "source_counts": {
            "crew_health_alerts": alert_counts["total"],
            "habitat_telemetry": habitat_audit_counts["total"],
        },
        "record_counts": {
            "total_evidence_records": total_evidence_records,
            "synthetic_records": synthetic_evidence_records,
            "non_synthetic_records": non_synthetic_evidence_records,
        },
        "retrieval": {
            "crew_findings": {
                "available": alert_counts["total"],
                "returned": len(crew_findings),
                "limit": FINDINGS_LIMIT,
                "truncated": alert_counts["total"] > len(crew_findings),
            },
            "habitat_suspect_findings": {
                "available": habitat_quality["SUSPECT"],
                "returned": len(habitat_findings),
                "limit": FINDINGS_LIMIT,
                "truncated": (
                    habitat_quality["SUSPECT"] > len(habitat_findings)
                ),
            },
        },
    }

    if alert_counts["critical_open"]:
        assessment_code = "OPEN_CRITICAL_HEALTH_ALERTS"
        assessment_text = (
            "Open critical health alerts exist in the stored mission records."
        )
    elif alert_counts["warning_open"]:
        assessment_code = "OPEN_WARNING_HEALTH_ALERTS"
        assessment_text = (
            "Open warning health alerts exist in the stored mission records."
        )
    elif habitat_quality["SUSPECT"]:
        assessment_code = "SUSPECT_HABITAT_DATA"
        assessment_text = (
            "Suspect habitat telemetry records require data review."
        )
    elif habitat_quality["UNGRADABLE"]:
        assessment_code = "DATA_QUALITY_REVIEW"
        assessment_text = (
            "Ungradable habitat records are present and require "
            "sensor or data-quality review."
        )
    else:
        assessment_code = "NO_FLAGGED_EVIDENCE"
        assessment_text = (
            "No flagged evidence was found in the evaluated records."
        )

    return {
        "audit_summary": audit_summary,
        "mission_assessment": {
            "code": assessment_code,
            "summary": assessment_text,
            "is_operational_decision": False,
        },
        "crew_findings": {
            "total_alerts": alert_counts["total"],
            "open_alerts": alert_counts["open"],
            "open_critical_alerts": alert_counts["critical_open"],
            "open_warning_alerts": alert_counts["warning_open"],
            "returned_count": len(crew_findings),
            "items": crew_findings,
        },
        "habitat_findings": {
            "quality_counts": habitat_quality,
            "suspect_records_available": habitat_quality["SUSPECT"],
            "returned_count": len(habitat_findings),
            "items": habitat_findings,
        },
        "evidence_policy": {
            "crew_source": "Persisted HealthAlert records.",
            "habitat_source": (
                "SUSPECT HabitatTelemetry records and simulator "
                "scenario descriptions."
            ),
            "ungradable_policy": (
                "UNGRADABLE habitat measurements are counted but "
                "excluded from environmental interpretations."
            ),
            "synthetic_data_warning": (
                "Simulator-generated records are illustrative synthetic "
                "data, not real spacecraft telemetry."
            ),
        },
        "disclaimer": (
            "Research software explainability output only. This is not "
            "a medical diagnosis, real-time spacecraft safety assessment, "
            "or validated operational decision system."
        ),
    }
