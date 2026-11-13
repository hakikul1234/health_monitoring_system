from django.db import models


class Astronaut(models.Model):

    class Status(models.TextChoices):
        TRAINING = "TRAINING", "Training"
        ACTIVE = "ACTIVE", "Active"
        ON_MISSION = "ON_MISSION", "On Mission"
        INACTIVE = "INACTIVE", "Inactive"

    profile = models.OneToOneField(
        "astra_accounts.UserProfile",
        on_delete=models.PROTECT,
        related_name="astronaut_record"
    )

    astronaut_code = models.CharField(
        max_length=30,
        unique=True
    )

    call_sign = models.CharField(
        max_length=80,
        blank=True
    )

    designation = models.CharField(
        max_length=100,
        blank=True
    )

    mission_specialization = models.CharField(
        max_length=120,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TRAINING
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Astronaut"
        verbose_name_plural = "Astronauts"

    def __str__(self):
        return f"{self.astronaut_code} - {self.profile.full_name}"
