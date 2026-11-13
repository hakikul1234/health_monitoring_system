from decimal import Decimal, InvalidOperation

from django.db import transaction

from astra_health.models import VitalSignReading
from astra_alerts.models import HealthAlert


PERSISTABLE_SEVERITIES = {
    "WARNING": HealthAlert.Severity.WARNING,
    "CRITICAL": HealthAlert.Severity.CRITICAL,
}


def _validate_reading(reading):
    if not isinstance(reading, VitalSignReading):
        raise TypeError(
            "reading must be a VitalSignReading instance."
        )

    if reading.pk is None or reading._state.adding:
        raise ValueError(
            "Reading must be saved before generating alerts."
        )


def _convert_observed_value(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(
            "Finding contains an invalid observed value."
        )

    if not result.is_finite():
        raise ValueError(
            "Observed value must be a finite decimal number."
        )

    return result.quantize(Decimal("0.01"))


@transaction.atomic
def generate_persistent_alerts(reading, analysis):
    """
    Persist WARNING and CRITICAL AI findings.

    This service is for synthetic software demonstration only.
    It does not create medical diagnoses or treatment decisions.

    Duplicate protection is provided by the database constraint:
    unique(reading, rule_code).
    """

    _validate_reading(reading)

    if not isinstance(analysis, dict):
        raise TypeError("analysis must be a dictionary.")

    # Data quality gate: never interpret ungradable readings.
    if str(reading.data_quality).endswith("UNGRADABLE"):
        return {
            "success": True,
            "message": "Ungradable reading skipped.",
            "created_count": 0,
            "existing_count": 0,
            "skipped_count": 0,
            "alerts": [],
        }

    if analysis.get("status") == "INSUFFICIENT_DATA":
        return {
            "success": True,
            "message": "Insufficient data. No alerts generated.",
            "created_count": 0,
            "existing_count": 0,
            "skipped_count": 0,
            "alerts": [],
        }

    findings = analysis.get("findings", [])

    if not isinstance(findings, list):
        raise ValueError(
            "Analysis findings must be a list."
        )

    created_count = 0
    existing_count = 0
    skipped_count = 0
    persisted_alerts = []

    for finding in findings:

        if not isinstance(finding, dict):
            raise ValueError(
                "Every finding must be a dictionary."
            )

        severity = str(
            finding.get("severity", "")
        ).upper()

        # Ignore NORMAL, UNKNOWN and unsupported severities.
        if severity not in PERSISTABLE_SEVERITIES:
            skipped_count += 1
            continue

        parameter = str(
            finding.get("parameter", "")
        ).strip()

        rule_code = str(
            finding.get("rule", "")
        ).strip()

        explanation = str(
            finding.get("explanation", "")
        ).strip()

        if not parameter or not rule_code or not explanation:
            raise ValueError(
                "Finding must contain parameter, rule and explanation."
            )

        observed_value = _convert_observed_value(
            finding.get("observed_value")
        )

        alert, created = HealthAlert.objects.get_or_create(
            reading=reading,
            rule_code=rule_code,
            defaults={
                "severity": PERSISTABLE_SEVERITIES[severity],
                "parameter": parameter,
                "observed_value": observed_value,
                "explanation": explanation,
                "is_synthetic": reading.is_synthetic,
            },
        )

        if created:
            created_count += 1
        else:
            existing_count += 1

        persisted_alerts.append({
            "id": alert.id,
            "severity": alert.severity,
            "parameter": alert.parameter,
            "rule_code": alert.rule_code,
            "observed_value": str(alert.observed_value),
            "status": alert.status,
            "created": created,
            "is_synthetic": alert.is_synthetic,
        })

    return {
        "success": True,
        "message": "AI alert generation completed.",
        "created_count": created_count,
        "existing_count": existing_count,
        "skipped_count": skipped_count,
        "alerts": persisted_alerts,
    }
