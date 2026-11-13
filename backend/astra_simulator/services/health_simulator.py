import random

from django.utils import timezone

from astra_health.models import VitalSignReading


SCENARIOS = {
    "NORMAL_MISSION": {
        "heart_rate_bpm": (65, 85),
        "spo2_percent": (96, 100),
        "body_temperature_c": (36.2, 37.2),
        "respiratory_rate_bpm": (12, 18),
        "data_quality": VitalSignReading.DataQuality.VALID,
        "quality_notes": "Synthetic normal mission telemetry.",
    },

    "HEALTH_ANOMALY": {
        "heart_rate_bpm": (110, 145),
        "spo2_percent": (88, 94),
        "body_temperature_c": (37.5, 38.5),
        "respiratory_rate_bpm": (22, 30),
        "data_quality": VitalSignReading.DataQuality.SUSPECT,
        "quality_notes": "Synthetic health anomaly scenario.",
    },

    "EMERGENCY_MISSION": {
        "heart_rate_bpm": (150, 180),
        "spo2_percent": (80, 87),
        "body_temperature_c": (38.6, 39.5),
        "respiratory_rate_bpm": (30, 40),
        "data_quality": VitalSignReading.DataQuality.SUSPECT,
        "quality_notes": "Synthetic emergency demonstration scenario.",
    },

    "DATA_QUALITY_FAULT": {
        "heart_rate_bpm": (65, 85),
        "spo2_percent": (96, 100),
        "body_temperature_c": (36.2, 37.2),
        "respiratory_rate_bpm": (12, 18),
        "data_quality": VitalSignReading.DataQuality.UNGRADABLE,
        "quality_notes": (
            "Synthetic data quality fault. "
            "Values are placeholders and must not be interpreted."
        ),
    },
}


def get_available_scenarios():
    """
    Return supported simulator scenario names.
    """
    return list(SCENARIOS.keys())


def generate_vital_sign_values(scenario, seed=None):
    """
    Generate synthetic vital signs for a selected scenario.

    A seed can be supplied to reproduce the same test values.
    """

    if scenario not in SCENARIOS:
        raise ValueError(
            f"Unsupported scenario: {scenario}. "
            f"Available scenarios: {get_available_scenarios()}"
        )

    rng = random.Random(seed)
    config = SCENARIOS[scenario]

    heart_rate = rng.randint(
        *config["heart_rate_bpm"]
    )

    spo2 = rng.randint(
        *config["spo2_percent"]
    )

    temperature = round(
        rng.uniform(*config["body_temperature_c"]),
        2
    )

    respiratory_rate = rng.randint(
        *config["respiratory_rate_bpm"]
    )

    return {
        "heart_rate_bpm": heart_rate,
        "spo2_percent": spo2,
        "body_temperature_c": temperature,
        "respiratory_rate_bpm": respiratory_rate,
        "data_quality": config["data_quality"],
        "quality_notes": config["quality_notes"],
    }


def create_simulated_reading(
    astronaut,
    mission=None,
    scenario="NORMAL_MISSION",
    seed=None,
):
    """
    Create one synthetic health reading in the database.

    All records created through this simulator are explicitly
    marked as synthetic.
    """

    if astronaut is None:
        raise ValueError("An astronaut is required.")

    if mission is not None:
        is_assigned = mission.crew.filter(
            pk=astronaut.pk
        ).exists()

        if not is_assigned:
            raise ValueError(
                "Astronaut is not assigned to the selected mission."
            )

    values = generate_vital_sign_values(
        scenario=scenario,
        seed=seed
    )

    reading = VitalSignReading.objects.create(
        astronaut=astronaut,
        mission=mission,
        heart_rate_bpm=values["heart_rate_bpm"],
        spo2_percent=values["spo2_percent"],
        body_temperature_c=values["body_temperature_c"],
        respiratory_rate_bpm=values["respiratory_rate_bpm"],
        recorded_at=timezone.now(),
        data_quality=values["data_quality"],
        data_source=VitalSignReading.DataSource.SIMULATOR,
        is_synthetic=True,
        quality_notes=values["quality_notes"],
    )

    return reading
