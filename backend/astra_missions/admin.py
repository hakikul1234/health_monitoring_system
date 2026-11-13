from django.contrib import admin

from .models import Mission


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):

    list_display = (
        "mission_code",
        "mission_name",
        "mission_type",
        "status",
        "destination",
        "planned_start_date",
        "planned_end_date",
        "created_by",
    )

    list_filter = (
        "mission_type",
        "status",
        "planned_start_date",
    )

    search_fields = (
        "mission_code",
        "mission_name",
        "destination",
    )

    filter_horizontal = (
        "crew",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )
