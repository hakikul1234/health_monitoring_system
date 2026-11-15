import random

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from astra_health.models import (
    VitalSignReading,
    VirtualHealthSensor,
    SensorSimulationRun,
)

from .health_simulator import (
    generate_vital_sign_values,
    get_available_scenarios,
)


MAX_BATCH_SIZE = 1000
MAX_INTERVAL_SECONDS = 3600

# Software-demo signal representation bounds.
# These are not clinical or diagnostic thresholds.
SIGNAL_BOUNDS = {
    "heart_rate_bpm": (1, 300),
    "spo2_percent": (1, 100),
    "body_temperature_c": (20.0, 60.0),
    "respiratory_rate_bpm": (1, 100),
}

# Explicit synthetic drift assumption, not a real sensor specification.
DRIFT_STEP_PERCENT = 0.25
DRIFT_MAX_PERCENT = 5.0


def _validate_request(count, interval_seconds, scenario, start_at):
    if not isinstance(count, int) or isinstance(count, bool):
        raise ValueError("Count must be an integer.")

    if count < 1 or count > MAX_BATCH_SIZE:
        raise ValueError(
            f"Count must be between 1 and {MAX_BATCH_SIZE}."
        )

    if (
        not isinstance(interval_seconds, int)
        or isinstance(interval_seconds, bool)
    ):
        raise ValueError("Interval must be an integer.")

    if interval_seconds < 1 or interval_seconds > MAX_INTERVAL_SECONDS:
        raise ValueError("Interval must be between 1 and 3600 seconds.")

    if scenario not in get_available_scenarios():
        raise ValueError(f"Unsupported scenario: {scenario}.")

    if start_at is not None and timezone.is_naive(start_at):
        raise ValueError("start_at must be timezone-aware.")


def _bounded_value(parameter, value):
    lower, upper = SIGNAL_BOUNDS[parameter]
    return max(lower, min(upper, value))


def _apply_noise(values, rng, noise_percent):
    result = dict(values)

    for parameter in SIGNAL_BOUNDS:
        original = float(values[parameter])
        amplitude = abs(original) * noise_percent / 100.0

        perturbed = original + rng.uniform(-amplitude, amplitude)
        perturbed = _bounded_value(parameter, perturbed)

        if parameter == "body_temperature_c":
            result[parameter] = round(perturbed, 2)
        else:
            result[parameter] = int(round(perturbed))

    return result


def _apply_drift(values, index, directions):
    result = dict(values)

    cumulative_percent = min(
        (index + 1) * DRIFT_STEP_PERCENT,
        DRIFT_MAX_PERCENT,
    )

    for parameter in SIGNAL_BOUNDS:
        original = float(values[parameter])

        drift = (
            original
            * cumulative_percent
            / 100.0
            * directions[parameter]
        )

        adjusted = _bounded_value(
            parameter,
            original + drift,
        )

        if parameter == "body_temperature_c":
            result[parameter] = round(adjusted, 2)
        else:
            result[parameter] = int(round(adjusted))

    return result


@transaction.atomic
def generate_virtual_sensor_run(
    sensor,
    scenario="NORMAL_MISSION",
    fault_mode=SensorSimulationRun.FaultMode.NORMAL,
    count=10,
    interval_seconds=60,
    seed=None,
    noise_level_percent=Decimal("0"),
    packet_loss_percent=Decimal("0"),
    start_at=None,
):
    """
    Generate an auditable synthetic virtual-sensor simulation run.

    Sensor faults are software simulation assumptions.
    This service does not represent validated hardware behavior.
    """

    if not isinstance(sensor, VirtualHealthSensor):
        raise TypeError("A VirtualHealthSensor instance is required.")

    if sensor.pk is None:
        raise ValueError("Sensor must be saved before simulation.")

    if sensor.status != VirtualHealthSensor.SensorStatus.ACTIVE:
        raise ValueError("Only ACTIVE registered sensors can be simulated.")

    _validate_request(
        count=count,
        interval_seconds=interval_seconds,
        scenario=scenario,
        start_at=start_at,
    )

    valid_fault_modes = [
        choice[0]
        for choice in SensorSimulationRun.FaultMode.choices
    ]

    if fault_mode not in valid_fault_modes:
        raise ValueError("Unsupported sensor fault mode.")

    noise_percent = Decimal(str(noise_level_percent))
    packet_loss = Decimal(str(packet_loss_percent))

    if not Decimal("0") <= noise_percent <= Decimal("100"):
        raise ValueError("Noise percentage must be between 0 and 100.")

    if not Decimal("0") <= packet_loss <= Decimal("100"):
        raise ValueError("Packet loss percentage must be between 0 and 100.")

    if (
        fault_mode != SensorSimulationRun.FaultMode.NOISE
        and noise_percent != 0
    ):
        raise ValueError("Noise percentage is only valid in NOISE mode.")

    if (
        fault_mode != SensorSimulationRun.FaultMode.DROPOUT
        and packet_loss != 0
    ):
        raise ValueError("Packet loss is only valid in DROPOUT mode.")

    if start_at is None:
        start_at = timezone.now() - timedelta(
            seconds=(count - 1) * interval_seconds
        )

    if timezone.is_naive(start_at):
        raise ValueError("start_at must be timezone-aware.")

    rng = random.Random(seed)

    directions = {
        parameter: rng.choice((-1, 1))
        for parameter in SIGNAL_BOUNDS
    }

    run = SensorSimulationRun.objects.create(
        sensor=sensor,
        fault_mode=fault_mode,
        seed=seed,
        noise_level_percent=noise_percent,
        packet_loss_percent=packet_loss,
        requested_count=count,
        generated_count=0,
        quality_counts={},
        status=SensorSimulationRun.RunStatus.NO_DATA,
        notes="Synthetic virtual sensor simulation.",
    )

    readings = []
    dropped_packets = 0

    if fault_mode != SensorSimulationRun.FaultMode.DISCONNECTED:

        for index in range(count):

            if (
                fault_mode == SensorSimulationRun.FaultMode.DROPOUT
                and rng.random() < float(packet_loss) / 100.0
            ):
                dropped_packets += 1
                continue

            sample_seed = rng.randrange(0, 2**32)

            values = generate_vital_sign_values(
                scenario=scenario,
                seed=sample_seed,
            )

            signal_values = {
                key: values[key]
                for key in SIGNAL_BOUNDS
            }

            fault_note = ""

            if fault_mode == SensorSimulationRun.FaultMode.NOISE:
                signal_values = _apply_noise(
                    signal_values,
                    rng,
                    float(noise_percent),
                )
                fault_note = " Synthetic signal noise applied."

            elif fault_mode == SensorSimulationRun.FaultMode.DRIFT:
                signal_values = _apply_drift(
                    signal_values,
                    index,
                    directions,
                )
                fault_note = (
                    " Synthetic gradual drift applied; "
                    f"assumed step {DRIFT_STEP_PERCENT}% per sample, "
                    f"capped at {DRIFT_MAX_PERCENT}%."
                )

            quality = values["data_quality"]

            if (
                fault_mode in (
                    SensorSimulationRun.FaultMode.NOISE,
                    SensorSimulationRun.FaultMode.DRIFT,
                )
                and quality != VitalSignReading.DataQuality.UNGRADABLE
            ):
                quality = VitalSignReading.DataQuality.SUSPECT

            notes = values["quality_notes"] + fault_note

            if fault_mode == SensorSimulationRun.FaultMode.DROPOUT:
                notes += " Packet delivery simulated with possible loss."

            readings.append(
                VitalSignReading(
                    astronaut=sensor.astronaut,
                    mission=sensor.mission,
                    sensor=sensor,
                    simulation_run=run,
                    heart_rate_bpm=signal_values["heart_rate_bpm"],
                    spo2_percent=signal_values["spo2_percent"],
                    body_temperature_c=signal_values["body_temperature_c"],
                    respiratory_rate_bpm=signal_values["respiratory_rate_bpm"],
                    recorded_at=start_at + timedelta(
                        seconds=index * interval_seconds
                    ),
                    data_quality=quality,
                    data_source=VitalSignReading.DataSource.SIMULATOR,
                    is_synthetic=True,
                    quality_notes=notes,
                )
            )

    saved_readings = VitalSignReading.objects.bulk_create(
        readings,
        batch_size=250,
    )

    quality_counts = {}

    for reading in saved_readings:
        quality = reading.data_quality
        quality_counts[quality] = quality_counts.get(quality, 0) + 1

    generated_count = len(saved_readings)

    if fault_mode == SensorSimulationRun.FaultMode.DISCONNECTED:
        run_status = SensorSimulationRun.RunStatus.NO_DATA
        notes = (
            "Sensor disconnection simulated for this run. "
            "No readings were generated. Registry status was not changed."
        )

    elif generated_count == 0:
        run_status = SensorSimulationRun.RunStatus.NO_DATA
        notes = (
            "No packets were delivered. "
            "No readings were fabricated."
        )

    elif generated_count < count:
        run_status = SensorSimulationRun.RunStatus.PARTIAL
        notes = (
            f"{dropped_packets} of {count} requested packets were dropped. "
            "Missing packets were not fabricated."
        )

    else:
        run_status = SensorSimulationRun.RunStatus.COMPLETED
        notes = "All requested synthetic packets were generated."

    run.generated_count = generated_count
    run.quality_counts = quality_counts
    run.status = run_status
    run.completed_at = timezone.now()
    run.notes = notes
    run.save(update_fields=[
        "generated_count",
        "quality_counts",
        "status",
        "completed_at",
        "notes",
    ])

    return {
        "run": run,
        "readings": saved_readings,
        "summary": {
            "requested_count": count,
            "generated_count": generated_count,
            "dropped_packets": dropped_packets,
            "quality_counts": quality_counts,
            "run_status": run.status,
            "all_synthetic": all(
                reading.is_synthetic
                for reading in saved_readings
            ),
            "fault_mode": fault_mode,
            "sensor_code": sensor.sensor_code,
            "disclaimer": (
                "Synthetic software simulation only. "
                "Fault parameters are illustrative assumptions, "
                "not validated sensor specifications or medical limits."
            ),
        },
    }
