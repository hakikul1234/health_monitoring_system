from django.db.models import Q
from rest_framework.exceptions import ValidationError

from astra_alerts.models import HealthAlert


def apply_alert_filters(queryset, params):

    severity = params.get("severity")
    alert_status = params.get("status")
    parameter = params.get("parameter")
    astronaut_code = params.get("astronaut_code")
    mission_code = params.get("mission_code")
    search = params.get("search")

    if severity:

        severity = severity.upper()

        valid_severities = {
            choice[0]
            for choice in HealthAlert.Severity.choices
        }

        if severity not in valid_severities:
            raise ValidationError({
                "severity": "Invalid severity filter."
            })

        queryset = queryset.filter(
            severity=severity
        )

    if alert_status:

        alert_status = alert_status.upper()

        valid_statuses = {
            choice[0]
            for choice in HealthAlert.Status.choices
        }

        if alert_status not in valid_statuses:
            raise ValidationError({
                "status": "Invalid alert status filter."
            })

        queryset = queryset.filter(
            status=alert_status
        )

    if parameter:

        queryset = queryset.filter(
            parameter__icontains=parameter
        )

    if astronaut_code:

        queryset = queryset.filter(
            reading__astronaut__astronaut_code__icontains=astronaut_code
        )

    if mission_code:

        queryset = queryset.filter(
            reading__mission__mission_code__icontains=mission_code
        )

    if search:

        queryset = queryset.filter(
            Q(rule_code__icontains=search)
            | Q(explanation__icontains=search)
            | Q(parameter__icontains=search)
            | Q(reading__astronaut__astronaut_code__icontains=search)
            | Q(reading__astronaut__profile__full_name__icontains=search)
            | Q(reading__mission__mission_code__icontains=search)
            | Q(reading__mission__mission_name__icontains=search)
        )

    return queryset.distinct()
