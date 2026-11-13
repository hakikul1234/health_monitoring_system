from django.contrib import admin

from .models import HealthAlert


@admin.register(HealthAlert)
class HealthAlertAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "severity",
        "parameter",
        "rule_code",
        "status",
        "reading",
        "is_synthetic",
        "created_at",
    )

    list_filter = (
        "severity",
        "status",
        "is_synthetic",
        "created_at",
    )

    search_fields = (
        "parameter",
        "rule_code",
        "explanation",
        "reading__astronaut__astronaut_code",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "is_synthetic",
    )

    date_hierarchy = "created_at"
