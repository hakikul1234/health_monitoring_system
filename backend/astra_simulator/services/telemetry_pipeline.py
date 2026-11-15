from django.db import transaction

from astra_health.ai.anomaly_detector import (
    detect_reading_anomalies,
)

from astra_alerts.services.alert_service import (
    generate_persistent_alerts,
)

from .telemetry_engine import (
    generate_telemetry_batch,
)


@transaction.atomic
def generate_telemetry_with_alerts(
    astronaut,
    mission=None,
    scenario="NORMAL_MISSION",
    count=10,
    interval_seconds=60,
    seed=None,
    start_at=None,
):
    """
    Generate synthetic telemetry and automatically persist
    explainable demonstration alerts.

    All reading generation and alert persistence are performed
    inside one database transaction.

    This is a software demonstration pipeline only.
    It is not a medical diagnostic or treatment system.
    """

    # ------------------------------------------------------
    # 1. GENERATE SYNTHETIC TELEMETRY
    # ------------------------------------------------------

    readings = generate_telemetry_batch(
        astronaut=astronaut,
        mission=mission,
        scenario=scenario,
        count=count,
        interval_seconds=interval_seconds,
        seed=seed,
        start_at=start_at,
    )

    # ------------------------------------------------------
    # 2. INITIALIZE PIPELINE STATISTICS
    # ------------------------------------------------------

    total_created = 0
    total_existing = 0
    total_skipped = 0

    normal_readings = 0
    insufficient_data_readings = 0
    analyzed_readings = 0

    severity_counts = {
        "WARNING": 0,
        "CRITICAL": 0,
    }

    persisted_alerts = []

    # ------------------------------------------------------
    # 3. ANALYZE EVERY SAVED READING
    # ------------------------------------------------------

    for reading in readings:

        analysis = detect_reading_anomalies(reading)

        analyzed_readings += 1

        if analysis.get("status") == "NORMAL":
            normal_readings += 1

        if analysis.get("status") == "INSUFFICIENT_DATA":
            insufficient_data_readings += 1

        # --------------------------------------------------
        # 4. PERSIST WARNING AND CRITICAL ALERTS
        # --------------------------------------------------

        result = generate_persistent_alerts(
            reading=reading,
            analysis=analysis,
        )

        total_created += result["created_count"]
        total_existing += result["existing_count"]
        total_skipped += result["skipped_count"]

        for alert in result["alerts"]:

            severity = alert["severity"]

            if severity in severity_counts:
                severity_counts[severity] += 1

            persisted_alerts.append(alert)

    # ------------------------------------------------------
    # 5. BUILD PIPELINE SUMMARY
    # ------------------------------------------------------

    alert_summary = {
        "success": True,

        "pipeline": "AUTOMATIC_AI_ALERT_GENERATION",

        "total_readings_analyzed": analyzed_readings,

        "normal_readings": normal_readings,

        "insufficient_data_readings": (
            insufficient_data_readings
        ),

        "created_alerts": total_created,

        "existing_alerts": total_existing,

        "skipped_findings": total_skipped,

        "severity_counts": severity_counts,

        "alerts": persisted_alerts,

        "all_readings_synthetic": all(
            reading.is_synthetic
            for reading in readings
        ),

        "disclaimer": (
            "Synthetic software demonstration only. "
            "Alerts are not medical diagnoses or "
            "treatment recommendations. "
            "Human review is required."
        ),
    }

    return readings, alert_summary


@transaction.atomic
def process_virtual_sensor_readings(
    readings,
    allow_health_alerts=True,
):
    """
    Reuse the existing anomaly detector and persistent alert service
    for virtual sensor readings.

    Sensor noise and drift must not independently create
    medical-style health alerts.
    """

    total_created = 0
    total_existing = 0
    total_skipped = 0

    normal_readings = 0
    insufficient_data_readings = 0
    analyzed_readings = 0

    severity_counts = {
        "WARNING": 0,
        "CRITICAL": 0,
    }

    persisted_alerts = []

    if not allow_health_alerts:
        return {
            "success": True,
            "pipeline": "SENSOR_FAULT_OBSERVATION_ONLY",
            "total_readings_analyzed": 0,
            "normal_readings": 0,
            "insufficient_data_readings": 0,
            "created_alerts": 0,
            "existing_alerts": 0,
            "skipped_findings": 0,
            "severity_counts": severity_counts,
            "alerts": [],
            "sensor_fault_readings_skipped": len(readings),
            "message": (
                "Health alert generation suppressed because "
                "the run contains simulated sensor noise or drift."
            ),
            "disclaimer": (
                "Sensor fault observations are not medical diagnoses. "
                "Human review is required."
            ),
        }

    for reading in readings:

        analysis = detect_reading_anomalies(reading)
        analyzed_readings += 1

        if analysis.get("status") == "NORMAL":
            normal_readings += 1

        if analysis.get("status") == "INSUFFICIENT_DATA":
            insufficient_data_readings += 1

        result = generate_persistent_alerts(
            reading=reading,
            analysis=analysis,
        )

        total_created += result["created_count"]
        total_existing += result["existing_count"]
        total_skipped += result["skipped_count"]

        for alert in result["alerts"]:
            severity = alert["severity"]

            if severity in severity_counts:
                severity_counts[severity] += 1

            persisted_alerts.append(alert)

    return {
        "success": True,
        "pipeline": "VIRTUAL_SENSOR_HEALTH_ALERT_GENERATION",
        "total_readings_analyzed": analyzed_readings,
        "normal_readings": normal_readings,
        "insufficient_data_readings": insufficient_data_readings,
        "created_alerts": total_created,
        "existing_alerts": total_existing,
        "skipped_findings": total_skipped,
        "severity_counts": severity_counts,
        "alerts": persisted_alerts,
        "sensor_fault_readings_skipped": 0,
        "all_readings_synthetic": all(
            reading.is_synthetic for reading in readings
        ),
        "disclaimer": (
            "Synthetic software demonstration only. "
            "Alerts are not medical diagnoses or treatment recommendations. "
            "Human review is required."
        ),
    }
