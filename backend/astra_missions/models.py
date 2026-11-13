from django.conf import settings
from django.db import models


class Mission(models.Model):

    class MissionType(models.TextChoices):
        ORBITAL = "ORBITAL", "Orbital Mission"
        LUNAR = "LUNAR", "Lunar Mission"
        DEEP_SPACE = "DEEP_SPACE", "Deep Space Mission"
        RESEARCH = "RESEARCH", "Research Mission"

    class Status(models.TextChoices):
        PLANNED = "PLANNED", "Planned"
        ACTIVE = "ACTIVE", "Active"
        COMPLETED = "COMPLETED", "Completed"
        ABORTED = "ABORTED", "Aborted"

    mission_code = models.CharField(
        max_length=40,
        unique=True
    )

    mission_name = models.CharField(
        max_length=150
    )

    mission_type = models.CharField(
        max_length=20,
        choices=MissionType.choices,
        default=MissionType.RESEARCH
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED
    )

    destination = models.CharField(
        max_length=150,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    objectives = models.TextField(
        blank=True
    )

    planned_start_date = models.DateField(
        null=True,
        blank=True
    )

    planned_end_date = models.DateField(
        null=True,
        blank=True
    )

    crew = models.ManyToManyField(
        "astra_crew.Astronaut",
        related_name="missions",
        blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_missions"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Mission"
        verbose_name_plural = "Missions"

    def __str__(self):
        return f"{self.mission_code} - {self.mission_name}"

    def clean(self):
        super().clean()

        if (
            self.planned_start_date
            and self.planned_end_date
            and self.planned_end_date < self.planned_start_date
        ):
            from django.core.exceptions import ValidationError

            raise ValidationError({
                "planned_end_date":
                    "Mission end date cannot be earlier than start date."
            })
