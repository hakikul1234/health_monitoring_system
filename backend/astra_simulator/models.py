from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class HabitatTelemetry(models.Model):

    class DataQuality(models.TextChoices):
        VALID = "VALID", "Valid"
        SUSPECT = "SUSPECT", "Suspect"
        UNGRADABLE = "UNGRADABLE", "Ungradable"

    mission = models.ForeignKey(
        "astra_missions.Mission",
        on_delete=models.PROTECT,
        related_name="habitat_readings"
    )

    sensor_id = models.CharField(
        max_length=64,
        default="SIM-HAB-01"
    )

    oxygen_partial_pressure_kpa = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )

    carbon_dioxide_ppm = models.PositiveIntegerField(
        validators=[
            MaxValueValidator(100000)
        ]
    )

    cabin_pressure_kpa = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(200)
        ]
    )

    cabin_temperature_c = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(-100),
            MaxValueValidator(100)
        ]
    )

    relative_humidity_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )

    scenario = models.CharField(
        max_length=40,
        default="NORMAL_HABITAT"
    )

    data_quality = models.CharField(
        max_length=20,
        choices=DataQuality.choices,
        default=DataQuality.VALID
    )

    recorded_at = models.DateTimeField()

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

        verbose_name = "Habitat Telemetry"
        verbose_name_plural = "Habitat Telemetry Records"

        indexes = [
            models.Index(
                fields=["mission", "recorded_at"],
                name="astra_hab_mission_time"
            ),
            models.Index(
                fields=["data_quality", "recorded_at"],
                name="astra_hab_quality_time"
            ),
            models.Index(
                fields=["is_synthetic", "recorded_at"],
                name="astra_hab_synth_time"
            ),
        ]

    def __str__(self):
        return (
            f"{self.mission.mission_code} | "
            f"{self.sensor_id} | "
            f"{self.recorded_at}"
        )
