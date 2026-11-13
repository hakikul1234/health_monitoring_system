from django.conf import settings
from django.db import models


class UserProfile(models.Model):

    class Role(models.TextChoices):
        ASTRONAUT = "ASTRONAUT", "Astronaut"
        MEDICAL_OFFICER = "MEDICAL_OFFICER", "Medical Officer"
        MISSION_CONTROL = "MISSION_CONTROL", "Mission Control"
        SYSTEM_ADMIN = "SYSTEM_ADMIN", "System Admin"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="astra_profile"
    )

    full_name = models.CharField(
        max_length=150,
        blank=True
    )

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.ASTRONAUT
    )

    badge_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
