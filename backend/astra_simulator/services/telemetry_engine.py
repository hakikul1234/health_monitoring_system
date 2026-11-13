import random

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from astra_health.models import VitalSignReading

from .health_simulator import (
    generate_vital_sign_values,
    get_available_scenarios,
)


MAX_BATCH_SIZE = 1000

DEFAULT_INTERVAL_SECONDS = 60


def generate_telemetry_batch(
    astronaut,
    mission=None,
    scenario="NORMAL_MISSION",
    count=10,
    interval_seconds=60,
    seed=None,
    start_at=None,
):
    """
    Generate a chronological batch of synthetic health readings.

    Parameters:
        astronaut:
            Astronaut model instance.

        mission:
            Optional Mission model instance.

        scenario:
            One of the supported simulator scenarios.

        count:
            Number of readings, from 1 to 1000.

        interval_seconds:
            Time difference between consecutive readings.

        seed:
            Optional seed for reproducible synthetic values.

        start_at:
            Optional timezone-aware starting timestamp.

    Returns:
        List of saved VitalSignReading instances.
    """

    # Validate astronaut

    if astronaut is None or not getattr(astronaut, "pk", None):
        raise ValueError("A saved astronaut instance is required.")

    # Validate batch size

    if not isinstance(count, int) or isinstance(count, bool):
        raise ValueError("Batch count must be an integer.")

    if count < 1 or count > MAX_BATCH_SIZE:
        raise ValueError(
            f"Batch count must be between 1 and {MAX_BATCH_SIZE}."
        )

    # Validate interval

    if (
        not isinstance(interval_seconds, int)
        or isinstance(interval_seconds, bool)
    ):
        raise ValueError("Interval must be an integer.")

    if interval_seconds < 1 or interval_seconds > 3600:
        raise ValueError(
            "Interval must be between 1 and 3600 seconds."
        )

    # Validate scenario

    if scenario not in get_available_scenarios():
        raise ValueError(
            f"Unsupported scenario: {scenario}."
        )

    # Validate mission assignment

    if mission is not None:

        if not getattr(mission, "pk", None):
            raise ValueError("Mission must be saved before use.")

        if not mission.crew.filter(pk=astronaut.pk).exists():
            raise ValueError(
                "Astronaut is not assigned to the selected mission."
            )

    # Validate starting timestamp

    if start_at is None:
        start_at = timezone.now() - timedelta(
            seconds=(count - 1) * interval_seconds
        )

    if timezone.is_naive(start_at):
        raise ValueError(
            "start_at must be a timezone-aware datetime."
        )

    # Reproducible seed handling

    rng = random.Random(seed)

    readings = []

    # Generate all readings in chronological order

    for index in range(count):

        reading_seed = rng.randrange(0, 2**32)

        values = generate_vital_sign_values(
            scenario=scenario,
            seed=reading_seed,
        )

        recorded_at = start_at + timedelta(
            seconds=index * interval_seconds
        )

        reading = VitalSignReading(
            astronaut=astronaut,
            mission=mission,
            heart_rate_bpm=values["heart_rate_bpm"],
            spo2_percent=values["spo2_percent"],
            body_temperature_c=values["body_temperature_c"],
            respiratory_rate_bpm=values["respiratory_rate_bpm"],
            recorded_at=recorded_at,
            data_quality=values["data_quality"],
            data_source=VitalSignReading.DataSource.SIMULATOR,
            is_synthetic=True,
            quality_notes=values["quality_notes"],
        )

        readings.append(reading)

    # Save batch atomically

    with transaction.atomic():

        saved_readings = VitalSignReading.objects.bulk_create(
            readings,
            batch_size=250,
        )

    return saved_readings


def get_telemetry_summary(readings):

    readings = list(readings)

    if not readings:
        return {
            "total_readings": 0,
            "first_recorded_at": None,
            "last_recorded_at": None,
            "average_heart_rate": None,
            "average_spo2": None,
            "data_quality_counts": {},
            "all_synthetic": True,
        }

    quality_counts = {}

    for reading in readings:

        quality = reading.data_quality

        quality_counts[quality] = (
            quality_counts.get(quality, 0) + 1
        )

    return {
        "total_readings": len(readings),

        "first_recorded_at": readings[0].recorded_at,

        "last_recorded_at": readings[-1].recorded_at,

        "average_heart_rate": round(
            sum(r.heart_rate_bpm for r in readings) / len(readings),
            2,
        ),

        "average_spo2": round(
            sum(r.spo2_percent for r in readings) / len(readings),
            2,
        ),

        "data_quality_counts": quality_counts,

        "all_synthetic": all(
            r.is_synthetic for r in readings
        ),
    }
