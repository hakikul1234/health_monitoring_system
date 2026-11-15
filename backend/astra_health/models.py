import uuid

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator




class VirtualHealthSensor(models.Model):

    class SensorStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        DEGRADED = "DEGRADED", "Degraded"
        DISCONNECTED = "DISCONNECTED", "Disconnected"

    class SensorType(models.TextChoices):
        CREW_WEARABLE = "CREW_WEARABLE", "Multi-parameter Crew Wearable"

    sensor_code = models.CharField(
        max_length=64,
        unique=True
    )

    astronaut = models.ForeignKey(
        "astra_crew.Astronaut",
        on_delete=models.PROTECT,
        related_name="virtual_health_sensors"
    )

    mission = models.ForeignKey(
        "astra_missions.Mission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="virtual_health_sensors"
    )

    sensor_type = models.CharField(
        max_length=30,
        choices=SensorType.choices,
        default=SensorType.CREW_WEARABLE
    )

    manufacturer = models.CharField(
        max_length=100,
        blank=True
    )

    model_number = models.CharField(
        max_length=100,
        blank=True
    )

    firmware_version = models.CharField(
        max_length=40,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=SensorStatus.choices,
        default=SensorStatus.ACTIVE
    )

    is_synthetic = models.BooleanField(
        default=True,
        editable=False
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sensor_code"]
        indexes = [
            models.Index(
                fields=["astronaut", "status"],
                name="astra_sensor_crew_status"
            ),
            models.Index(
                fields=["mission", "status"],
                name="astra_sensor_mission_status"
            ),
        ]

    def __str__(self):
        return f"{self.sensor_code} | {self.status}"


class SensorSimulationRun(models.Model):

    class FaultMode(models.TextChoices):
        NORMAL = "NORMAL", "Normal Signal"
        NOISE = "NOISE", "Signal Noise"
        DROPOUT = "DROPOUT", "Packet Dropout"
        DRIFT = "DRIFT", "Signal Drift"
        DISCONNECTED = "DISCONNECTED", "Sensor Disconnected"

    class RunStatus(models.TextChoices):
        COMPLETED = "COMPLETED", "Completed"
        PARTIAL = "PARTIAL", "Partially Completed"
        NO_DATA = "NO_DATA", "No Readings Generated"

    run_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    sensor = models.ForeignKey(
        VirtualHealthSensor,
        on_delete=models.PROTECT,
        related_name="simulation_runs"
    )

    fault_mode = models.CharField(
        max_length=20,
        choices=FaultMode.choices,
        default=FaultMode.NORMAL
    )

    seed = models.BigIntegerField(
        null=True,
        blank=True
    )

    noise_level_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )

    packet_loss_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )

    requested_count = models.PositiveSmallIntegerField(default=0)
    generated_count = models.PositiveSmallIntegerField(default=0)

    quality_counts = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=20,
        choices=RunStatus.choices,
        default=RunStatus.COMPLETED
    )

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    is_synthetic = models.BooleanField(
        default=True,
        editable=False
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(
                fields=["sensor", "started_at"],
                name="astra_run_sensor_time"
            ),
            models.Index(
                fields=["fault_mode", "started_at"],
                name="astra_run_fault_time"
            ),
        ]

    def __str__(self):
        return f"{self.run_id} | {self.fault_mode} | {self.status}"


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

    sensor = models.ForeignKey(
        "VirtualHealthSensor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="readings"
    )

    simulation_run = models.ForeignKey(
        "SensorSimulationRun",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="readings"
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
