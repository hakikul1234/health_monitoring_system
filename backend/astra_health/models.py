import uuid

from django.db import models


class VitalSignReading(models.Model):

    class DataQuality(models.TextChoices):
        VALID = "VALID", "Valid"
        SUSPECT = "SUSPECT", "Suspect"
        UNGRADABLE = "UNGRADABLE", "Ungradable"

    class DataSource(models.TextChoices):
        SIMULATOR = "SIMULATOR", "Virtual Sensor Simulator"
        TEST_FIXTURE = "TEST_FIXTURE", "Synthetic Test Fixture"

    sample_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    astronaut = models.ForeignKey(
        "astra_crew.Astronaut",
        on_delete=models.PROTECT,
        related_name="health_readings"
    )

    mission = models.ForeignKey(
        "astra_missions.Mission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="health_readings"
    )

    heart_rate_bpm = models.PositiveSmallIntegerField()

    spo2_percent = models.PositiveSmallIntegerField()

    body_temperature_c = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    respiratory_rate_bpm = models.PositiveSmallIntegerField()

    recorded_at = models.DateTimeField()

    data_quality = models.CharField(
        max_length=20,
        choices=DataQuality.choices,
        default=DataQuality.VALID
    )

    data_source = models.CharField(
        max_length=20,
        choices=DataSource.choices,
        default=DataSource.SIMULATOR
    )

    is_synthetic = models.BooleanField(
        default=True,
        editable=False
    )

    quality_notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-recorded_at"]

        verbose_name = "Vital Sign Reading"
        verbose_name_plural = "Vital Sign Readings"

        indexes = [
            models.Index(
                fields=["astronaut", "recorded_at"],
                name="astra_health_crew_time"
            ),
            models.Index(
                fields=["is_synthetic", "recorded_at"],
                name="astra_health_synth_time"
            ),
            models.Index(
                fields=["mission", "recorded_at"],
                name="astra_health_mission_time"
            ),
            models.Index(
                fields=["data_quality"],
                name="astra_health_quality"
            ),
        ]

    def __str__(self):
        return (
            f"{self.astronaut.astronaut_code} | "
            f"{self.recorded_at} | "
            f"HR: {self.heart_rate_bpm} BPM"
        )
