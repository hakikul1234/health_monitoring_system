from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Count, Q
from django.utils import timezone

from astra_accounts.models import UserProfile
from astra_crew.models import Astronaut
from astra_missions.models import Mission
from astra_health.models import VitalSignReading
from astra_alerts.models import HealthAlert


def get_dashboard_analytics(user):
    """
    Build role-scoped Mission Control dashboard analytics.

    All health readings and alerts are synthetic software
    demonstration records. These statistics are not clinical
    assessments or diagnostic outputs.
    """

    if not user or not user.is_authenticated:
        raise PermissionDenied("Authenticated user required.")

    try:
        role = user.astra_profile.role
    except ObjectDoesNotExist:
        raise PermissionDenied("User profile not found.")

    # ------------------------------------------------------
    # 1. ROLE-SCOPED QUERYSETS
    # ------------------------------------------------------

    astronauts = Astronaut.objects.select_related(
        "profile",
        "profile__user",
    )

    missions = Mission.objects.prefetch_related("crew")

    readings = VitalSignReading.objects.select_related(
        "astronaut",
        "astronaut__profile",
        "mission",
    ).filter(
        is_synthetic=True
    )

    alerts = HealthAlert.objects.select_related(
        "reading",
        "reading__astronaut",
        "reading__astronaut__profile",
        "reading__mission",
    ).filter(
        is_synthetic=True
    )

    if role == UserProfile.Role.ASTRONAUT:

        astronauts = astronauts.filter(
            profile__user=user
        )

        missions = missions.filter(
            crew__profile__user=user
        ).distinct()

        readings = readings.filter(
            astronaut__profile__user=user
        )

        alerts = alerts.filter(
            reading__astronaut__profile__user=user
        )

    elif role in {
        UserProfile.Role.MEDICAL_OFFICER,
        UserProfile.Role.MISSION_CONTROL,
        UserProfile.Role.SYSTEM_ADMIN,
    }:
        pass

    else:
        raise PermissionDenied("Unsupported dashboard role.")

    # ------------------------------------------------------
    # 2. CREW STATISTICS
    # ------------------------------------------------------

    crew_stats = astronauts.aggregate(
        total=Count("id"),

        active=Count(
            "id",
            filter=Q(status=Astronaut.Status.ACTIVE),
        ),

        on_mission=Count(
            "id",
            filter=Q(status=Astronaut.Status.ON_MISSION),
        ),

        training=Count(
            "id",
            filter=Q(status=Astronaut.Status.TRAINING),
        ),

        inactive=Count(
            "id",
            filter=Q(status=Astronaut.Status.INACTIVE),
        ),
    )

    # ------------------------------------------------------
    # 3. MISSION STATISTICS
    # ------------------------------------------------------

    mission_stats = missions.aggregate(
        total=Count("id"),

        planned=Count(
            "id",
            filter=Q(status=Mission.Status.PLANNED),
        ),

        active=Count(
            "id",
            filter=Q(status=Mission.Status.ACTIVE),
        ),

        completed=Count(
            "id",
            filter=Q(status=Mission.Status.COMPLETED),
        ),

        aborted=Count(
            "id",
            filter=Q(status=Mission.Status.ABORTED),
        ),
    )

    # ------------------------------------------------------
    # 4. HEALTH READING STATISTICS
    # ------------------------------------------------------

    health_stats = readings.aggregate(
        total=Count("id"),

        valid=Count(
            "id",
            filter=Q(
                data_quality=VitalSignReading.DataQuality.VALID
            ),
        ),

        suspect=Count(
            "id",
            filter=Q(
                data_quality=VitalSignReading.DataQuality.SUSPECT
            ),
        ),

        ungradable=Count(
            "id",
            filter=Q(
                data_quality=VitalSignReading.DataQuality.UNGRADABLE
            ),
        ),
    )

    # ------------------------------------------------------
    # 5. HEALTH ALERT STATISTICS
    # ------------------------------------------------------

    alert_stats = alerts.aggregate(
        total=Count("id"),

        open=Count(
            "id",
            filter=Q(status=HealthAlert.Status.OPEN),
        ),

        acknowledged=Count(
            "id",
            filter=Q(status=HealthAlert.Status.ACKNOWLEDGED),
        ),

        resolved=Count(
            "id",
            filter=Q(status=HealthAlert.Status.RESOLVED),
        ),

        warning=Count(
            "id",
            filter=Q(severity=HealthAlert.Severity.WARNING),
        ),

        critical=Count(
            "id",
            filter=Q(severity=HealthAlert.Severity.CRITICAL),
        ),
    )

    # ------------------------------------------------------
    # 6. LATEST HEALTH READINGS
    # ------------------------------------------------------

    latest_readings = readings.order_by(
        "-recorded_at"
    )[:10]

    latest_reading_data = []

    for reading in latest_readings:

        latest_reading_data.append({
            "id": reading.id,

            "astronaut_code": (
                reading.astronaut.astronaut_code
            ),

            "astronaut_name": (
                reading.astronaut.profile.full_name
            ),

            "mission_code": (
                reading.mission.mission_code
                if reading.mission else None
            ),

            "heart_rate_bpm": reading.heart_rate_bpm,

            "spo2_percent": reading.spo2_percent,

            "body_temperature_c": str(
                reading.body_temperature_c
            ),

            "respiratory_rate_bpm": (
                reading.respiratory_rate_bpm
            ),

            "data_quality": reading.data_quality,

            "recorded_at": reading.recorded_at.isoformat(),

            "is_synthetic": reading.is_synthetic,
        })

    # ------------------------------------------------------
    # 7. LATEST CRITICAL ALERTS
    # ------------------------------------------------------

    latest_critical_alerts = alerts.filter(
        severity=HealthAlert.Severity.CRITICAL
    ).order_by(
        "-created_at"
    )[:10]

    critical_alert_data = []

    for alert in latest_critical_alerts:

        critical_alert_data.append({
            "id": alert.id,

            "astronaut_code": (
                alert.reading.astronaut.astronaut_code
            ),

            "astronaut_name": (
                alert.reading.astronaut.profile.full_name
            ),

            "mission_code": (
                alert.reading.mission.mission_code
                if alert.reading.mission else None
            ),

            "parameter": alert.parameter,

            "rule_code": alert.rule_code,

            "observed_value": str(alert.observed_value),

            "severity": alert.severity,

            "status": alert.status,

            "explanation": alert.explanation,

            "created_at": alert.created_at.isoformat(),

            "is_synthetic": alert.is_synthetic,
        })

    # ------------------------------------------------------
    # 8. MISSION-WISE HEALTH SUMMARY
    # ------------------------------------------------------

    # ------------------------------------------------------
    # 8. MISSION-WISE HEALTH SUMMARY
    # ------------------------------------------------------

    reading_scope_filter = Q(
        health_readings__is_synthetic=True
    )

    open_alert_scope_filter = Q(
        health_readings__health_alerts__is_synthetic=True,
        health_readings__health_alerts__status=(
            HealthAlert.Status.OPEN
        ),
    )

    critical_alert_scope_filter = Q(
        health_readings__health_alerts__is_synthetic=True,
        health_readings__health_alerts__severity=(
            HealthAlert.Severity.CRITICAL
        ),
    )

    # Astronauts must only see their own health
    # readings and alerts inside mission summaries.

    if role == UserProfile.Role.ASTRONAUT:

        astronaut_scope = Q(
            health_readings__astronaut__profile__user=user
        )

        reading_scope_filter &= astronaut_scope

        open_alert_scope_filter &= astronaut_scope

        critical_alert_scope_filter &= astronaut_scope

    mission_summary_queryset = missions.annotate(

        crew_count=Count(
            "crew",
            distinct=True,
        ),

        reading_count=Count(
            "health_readings",
            filter=reading_scope_filter,
            distinct=True,
        ),

        open_alert_count=Count(
            "health_readings__health_alerts",
            filter=open_alert_scope_filter,
            distinct=True,
        ),

        critical_alert_count=Count(
            "health_readings__health_alerts",
            filter=critical_alert_scope_filter,
            distinct=True,
        ),

    ).order_by(
        "-created_at"
    )[:10]

    mission_summary = []

    for mission in mission_summary_queryset:

        mission_summary.append({
            "id": mission.id,

            "mission_code": mission.mission_code,

            "mission_name": mission.mission_name,

            "mission_type": mission.mission_type,

            "status": mission.status,

            "destination": mission.destination,

            "crew_count": mission.crew_count,

            "reading_count": mission.reading_count,

            "open_alert_count": mission.open_alert_count,

            "critical_alert_count": (
                mission.critical_alert_count
            ),
        })

    # ------------------------------------------------------
    # 9. FINAL DASHBOARD RESPONSE
    # ------------------------------------------------------

    return {
        "success": True,

        "generated_at": timezone.now().isoformat(),

        "user_role": role,

        "crew": crew_stats,

        "missions": mission_stats,

        "health": health_stats,

        "alerts": alert_stats,

        "latest_readings": latest_reading_data,

        "latest_critical_alerts": critical_alert_data,

        "mission_summary": mission_summary,

        "data_scope": (
            "OWN_RECORDS"
            if role == UserProfile.Role.ASTRONAUT
            else "AUTHORIZED_GLOBAL_RECORDS"
        ),

        "disclaimer": (
            "All health readings and alerts are synthetic "
            "software demonstration data. Dashboard analytics "
            "are not clinically validated and must not be used "
            "for diagnosis or treatment decisions. "
            "Human review is required."
        ),
    }
