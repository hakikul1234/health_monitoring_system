from django.contrib import admin

from .models import VitalSignReading


@admin.register(VitalSignReading)
class VitalSignReadingAdmin(admin.ModelAdmin):

    list_display = (
        "sample_id",
        "astronaut",
        "mission",
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
