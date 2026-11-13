from django.contrib import admin

from .models import UserProfile
from astra_crew.models import Astronaut


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "full_name",
        "role",
        "badge_id",
        "created_at",
    )

    list_filter = (
        "role",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "full_name",
        "badge_id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Astronaut)
class AstronautAdmin(admin.ModelAdmin):

    list_display = (
        "astronaut_code",
        "profile",
        "call_sign",
        "designation",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "designation",
    )

    search_fields = (
        "astronaut_code",
        "call_sign",
        "profile__full_name",
        "profile__user__username",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )
