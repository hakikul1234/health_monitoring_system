from django.contrib import admin

from .models import VitalSignReading, VirtualHealthSensor, SensorSimulationRun


@admin.register(VitalSignReading)
class VitalSignReadingAdmin(admin.ModelAdmin):

    list_display = (
        "sample_id",
        "astronaut",
        "mission",
        "sensor",
        "simulation_run",
        "heart_rate_bpm",
        "spo2_percent",
        "body_temperature_c",
        "respiratory_rate_bpm",
        "data_quality",
        "is_synthetic",
        "recorded_at",
    )

    list_filter = (
        "data_quality",
        "data_source",
        "sensor",
        "is_synthetic",
        "recorded_at",
    )

    search_fields = (
        "astronaut__astronaut_code",
        "astronaut__profile__full_name",
        "mission__mission_code",
    )

    readonly_fields = (
        "sample_id",
        "created_at",
        "is_synthetic",
    )

    date_hierarchy = "recorded_at"



@admin.register(VirtualHealthSensor)
class VirtualHealthSensorAdmin(admin.ModelAdmin):

    list_display = (
        "sensor_code",
        "astronaut",
        "mission",
        "sensor_type",
        "status",
        "is_synthetic",
        "created_at",
    )

    list_filter = (
        "status",
        "sensor_type",
        "is_synthetic",
    )

    search_fields = (
        "sensor_code",
        "astronaut__astronaut_code",
        "astronaut__profile__full_name",
        "mission__mission_code",
        "manufacturer",
        "model_number",
    )

    readonly_fields = (
        "is_synthetic",
        "created_at",
        "updated_at",
    )


@admin.register(SensorSimulationRun)
class SensorSimulationRunAdmin(admin.ModelAdmin):

    list_display = (
        "run_id",
        "sensor",
        "fault_mode",
        "status",
        "requested_count",
        "generated_count",
        "is_synthetic",
        "started_at",
    )

    list_filter = (
        "fault_mode",
        "status",
        "is_synthetic",
        "started_at",
    )

    search_fields = (
        "run_id",
        "sensor__sensor_code",
        "notes",
    )

    readonly_fields = (
        "run_id",
        "is_synthetic",
        "started_at",
    )
