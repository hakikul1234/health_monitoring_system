from django.conf import settings
from django.db import models


class HealthAlert(models.Model):

    class Severity(models.TextChoices):
        WARNING = "WARNING", "Warning"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        RESOLVED = "RESOLVED", "Resolved"

    reading = models.ForeignKey(
        "astra_health.VitalSignReading",
        on_delete=models.PROTECT,
        related_name="health_alerts"
    )

    severity = models.CharField(
        max_length=20,
        choices=Severity.choices
    )

    parameter = models.CharField(
        max_length=60
    )

    rule_code = models.CharField(
        max_length=100
    )

    observed_value = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    explanation = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )

    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_health_alerts"
    )

    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True
    )

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_health_alerts"
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True
    )

    resolution_notes = models.TextField(
        blank=True
    )

    is_synthetic = models.BooleanField(
        default=True,
        editable=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

        verbose_name = "Health Alert"
        verbose_name_plural = "Health Alerts"

        constraints = [
            models.UniqueConstraint(
                fields=["reading", "rule_code"],
                name="unique_reading_alert_rule"
            )
        ]

        indexes = [
            models.Index(
                fields=["status", "severity"],
                name="astra_alert_status_sev"
            ),
            models.Index(
                fields=["is_synthetic", "severity", "created_at"],
                name="astra_alert_synth_sev_time"
            ),
            models.Index(
                fields=["created_at"],
                name="astra_alert_created"
            ),
        ]

    def __str__(self):
        return (
            f"{self.severity} | "
            f"{self.parameter} | "
            f"Reading #{self.reading_id}"
        )
