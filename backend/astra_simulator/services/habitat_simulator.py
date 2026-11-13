import random

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from astra_simulator.models import HabitatTelemetry


MAX_BATCH_SIZE = 1000


HABITAT_SCENARIOS = {
    "NORMAL_HABITAT": {
        "description": "Illustrative nominal habitat conditions.",
        "data_quality": "VALID",
    },
    "ELEVATED_CO2": {
        "description": "Elevated synthetic cabin carbon dioxide.",
        "data_quality": "SUSPECT",
    },
    "PRESSURE_DEVIATION": {
        "description": "Synthetic cabin pressure deviation.",
        "data_quality": "SUSPECT",
    },
    "TEMPERATURE_HUMIDITY_ANOMALY": {
        "description": "Synthetic temperature and humidity anomaly.",
        "data_quality": "SUSPECT",
    },
    "SENSOR_QUALITY_FAULT": {
        "description": "Simulated sensor quality failure; values are placeholders.",
        "data_quality": "UNGRADABLE",
    },
}


def get_available_habitat_scenarios():
    return list(HABITAT_SCENARIOS.keys())


def _decimal_value(rng, minimum, maximum):
    value = round(rng.uniform(minimum, maximum), 2)
    return Decimal(str(value))


def generate_habitat_values(scenario, seed=None):
    """
    Generate one deterministic synthetic habitat telemetry sample.

    All ranges are illustrative software-demo values.
    They are not spacecraft operating limits or safety thresholds.
    """

    if scenario not in HABITAT_SCENARIOS:
        raise ValueError(
            f"Unsupported habitat scenario: {scenario}."
        )

    rng = random.Random(seed)

    values = {
        "oxygen_partial_pressure_kpa": _decimal_value(
            rng, 19.0, 23.7
        ),
        "carbon_dioxide_ppm": rng.randint(400, 2000),
        "cabin_pressure_kpa": _decimal_value(
            rng, 95.0, 103.0
        ),
        "cabin_temperature_c": _decimal_value(
            rng, 19.0, 25.0
        ),
        "relative_humidity_percent": _decimal_value(
            rng, 30.0, 60.0
        ),
        "data_quality": HABITAT_SCENARIOS[scenario]["data_quality"],
        "quality_notes": "",
    }

    if scenario == "ELEVATED_CO2":
        values["carbon_dioxide_ppm"] = rng.randint(
            5000, 15000
        )
        values["quality_notes"] = (
            "Synthetic elevated CO2 demonstration scenario."
        )

    elif scenario == "PRESSURE_DEVIATION":
        if rng.choice(["LOW", "HIGH"]) == "LOW":
            values["cabin_pressure_kpa"] = _decimal_value(
                rng, 45.0, 60.0
            )
        else:
            values["cabin_pressure_kpa"] = _decimal_value(
                rng, 115.0, 130.0
            )

        values["quality_notes"] = (
            "Synthetic cabin pressure deviation scenario."
        )

    elif scenario == "TEMPERATURE_HUMIDITY_ANOMALY":
        values["cabin_temperature_c"] = _decimal_value(
            rng, 30.0, 40.0
        )
        values["relative_humidity_percent"] = _decimal_value(
            rng, 75.0, 95.0
        )
        values["quality_notes"] = (
            "Synthetic temperature and humidity anomaly."
        )

    elif scenario == "SENSOR_QUALITY_FAULT":
        values["quality_notes"] = (
            "UNGRADABLE: generated measurements are placeholders. "
            "Do not interpret them as valid environmental readings."
        )

    return values


def generate_habitat_telemetry_batch(
    mission,
    scenario="NORMAL_HABITAT",
    count=10,
    interval_seconds=60,
    seed=None,
    start_at=None,
    sensor_id="SIM-HAB-01",
):
    """
    Generate and atomically save a chronological habitat batch.
    """

    if mission is None or not getattr(mission, "pk", None):
        raise ValueError("A saved mission instance is required.")

    if not isinstance(count, int) or isinstance(count, bool):
        raise ValueError("Batch count must be an integer.")

    if count < 1 or count > MAX_BATCH_SIZE:
        raise ValueError(
            f"Batch count must be between 1 and {MAX_BATCH_SIZE}."
        )

    if (
        not isinstance(interval_seconds, int)
        or isinstance(interval_seconds, bool)
    ):
        raise ValueError("Interval must be an integer.")

    if interval_seconds < 1 or interval_seconds > 3600:
        raise ValueError(
            "Interval must be between 1 and 3600 seconds."
        )

    if scenario not in HABITAT_SCENARIOS:
        raise ValueError(
            f"Unsupported habitat scenario: {scenario}."
        )

    if not isinstance(sensor_id, str) or not sensor_id.strip():
        raise ValueError("A valid sensor_id is required.")

    if len(sensor_id) > 64:
        raise ValueError("sensor_id cannot exceed 64 characters.")

    if start_at is None:
        start_at = timezone.now() - timedelta(
            seconds=(count - 1) * interval_seconds
        )

    if timezone.is_naive(start_at):
        raise ValueError(
            "start_at must be a timezone-aware datetime."
        )

    rng = random.Random(seed)
    records = []

    for index in range(count):
        sample_seed = rng.randrange(0, 2**32)

        values = generate_habitat_values(
            scenario=scenario,
            seed=sample_seed,
        )

        records.append(
            HabitatTelemetry(
                mission=mission,
                sensor_id=sensor_id,
                oxygen_partial_pressure_kpa=(
                    values["oxygen_partial_pressure_kpa"]
                ),
                carbon_dioxide_ppm=(
                    values["carbon_dioxide_ppm"]
                ),
                cabin_pressure_kpa=(
                    values["cabin_pressure_kpa"]
                ),
                cabin_temperature_c=(
                    values["cabin_temperature_c"]
                ),
                relative_humidity_percent=(
                    values["relative_humidity_percent"]
                ),
                scenario=scenario,
                data_quality=values["data_quality"],
                recorded_at=(
                    start_at + timedelta(
                        seconds=index * interval_seconds
                    )
                ),
                is_synthetic=True,
                quality_notes=values["quality_notes"],
            )
        )

    with transaction.atomic():
        saved_records = HabitatTelemetry.objects.bulk_create(
            records,
            batch_size=250,
        )

    return saved_records


def get_habitat_telemetry_summary(records):
    """
    Summarize habitat telemetry without interpreting UNGRADABLE
    sensor placeholder values as environmental measurements.

    VALID and SUSPECT readings are included in averages.
    All readings remain included in totals and quality counts.
    """
    records = list(records)

    if not records:
        return {
            "total_readings": 0,
            "first_recorded_at": None,
            "last_recorded_at": None,
            "average_oxygen_partial_pressure_kpa": None,
            "average_carbon_dioxide_ppm": None,
            "average_cabin_pressure_kpa": None,
            "average_cabin_temperature_c": None,
            "average_relative_humidity_percent": None,
            "data_quality_counts": {},
            "all_synthetic": True,
        }

    quality_counts = {}

    for record in records:
        quality = record.data_quality
        quality_counts[quality] = quality_counts.get(quality, 0) + 1

    usable_records = [
        record
        for record in records
        if record.data_quality != HabitatTelemetry.DataQuality.UNGRADABLE
    ]

    if usable_records:
        usable_count = len(usable_records)

        average_oxygen = round(
            sum(
                float(record.oxygen_partial_pressure_kpa)
                for record in usable_records
            ) / usable_count,
            2,
        )

        average_co2 = round(
            sum(
                record.carbon_dioxide_ppm
                for record in usable_records
            ) / usable_count,
            2,
        )

        average_pressure = round(
            sum(
                float(record.cabin_pressure_kpa)
                for record in usable_records
            ) / usable_count,
            2,
        )

        average_temperature = round(
            sum(
                float(record.cabin_temperature_c)
                for record in usable_records
            ) / usable_count,
            2,
        )

        average_humidity = round(
            sum(
                float(record.relative_humidity_percent)
                for record in usable_records
            ) / usable_count,
            2,
        )
    else:
        average_oxygen = None
        average_co2 = None
        average_pressure = None
        average_temperature = None
        average_humidity = None

    return {
        "total_readings": len(records),
        "first_recorded_at": records[0].recorded_at,
        "last_recorded_at": records[-1].recorded_at,
        "average_oxygen_partial_pressure_kpa": average_oxygen,
        "average_carbon_dioxide_ppm": average_co2,
        "average_cabin_pressure_kpa": average_pressure,
        "average_cabin_temperature_c": average_temperature,
        "average_relative_humidity_percent": average_humidity,
        "data_quality_counts": quality_counts,
        "all_synthetic": all(
            record.is_synthetic for record in records
        ),
    }
