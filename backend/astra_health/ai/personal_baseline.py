"""
Personal baseline intelligence for ASTRA-PULSE AI.

Uses historical VALID synthetic readings belonging to the
same astronaut. This is a research software demonstration,
not a medical diagnostic or risk prediction system.
"""

import math
from datetime import timedelta

from django.utils import timezone

from astra_health.models import VitalSignReading


FEATURES = (
    "heart_rate_bpm",
    "spo2_percent",
    "body_temperature_c",
    "respiratory_rate_bpm",
)

MIN_BASELINE_READINGS = 10
MAX_BASELINE_READINGS = 100
BASELINE_WINDOW_DAYS = 30
ROBUST_Z_THRESHOLD = 3.5
MAD_NORMALIZATION = 0.6744897501960817


def _not_evaluated(status, explanation, quality=None):
    return {
        "enabled": True,
        "status": status,
        "astronaut_id": None,
        "baseline_readings": 0,
        "minimum_required": MIN_BASELINE_READINGS,
        "window_days": BASELINE_WINDOW_DAYS,
        "features": {},
        "clinical_validation": False,
        "data_quality": quality,
        "explanation": explanation,
    }


def _finite_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return number


def _median(values):
    ordered = sorted(values)
    count = len(ordered)
    middle = count // 2

    if count % 2:
        return ordered[middle]

    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _calculate_feature(current_value, historical_values):
    center = _median(historical_values)

    absolute_deviations = [
        abs(value - center)
        for value in historical_values
    ]

    mad = _median(absolute_deviations)
    difference = current_value - center

    if mad == 0:
        return {
            "baseline_median": center,
            "baseline_mad": 0.0,
            "current_value": current_value,
            "difference_from_baseline": difference,
            "robust_z_score": None,
            "deviation_detected": None,
            "status": "ZERO_MAD",
            "explanation": (
                "Historical median absolute deviation is zero. "
                "A reliable robust Z-score cannot be calculated "
                "for this feature."
            ),
        }

    robust_z = (
        MAD_NORMALIZATION * difference / mad
    )

    detected = abs(robust_z) >= ROBUST_Z_THRESHOLD

    return {
        "baseline_median": round(center, 4),
        "baseline_mad": round(mad, 4),
        "current_value": current_value,
        "difference_from_baseline": round(difference, 4),
        "robust_z_score": round(robust_z, 4),
        "deviation_detected": detected,
        "status": (
            "DEVIATION" if detected else "WITHIN_BASELINE"
        ),
        "explanation": (
            "Absolute robust Z-score meets or exceeds "
            "the configured research threshold."
            if detected
            else
            "Absolute robust Z-score is below the "
            "configured research threshold."
        ),
    }


def calculate_personal_baseline(
    reading,
    historical_readings,
):
    """
    Calculate a per-astronaut baseline from prior readings.

    historical_readings must contain readings belonging to
    the same astronaut, earlier than the current reading,
    within the configured time window, and VALID synthetic.
    """

    if not bool(getattr(reading, "is_synthetic", False)):
        return _not_evaluated(
            "NOT_EVALUATED",
            "Personal baseline analysis is restricted to "
            "synthetic demonstration telemetry.",
        )

    quality = str(
        getattr(reading, "data_quality", "")
    ).split(".")[-1].upper()

    if quality == "UNGRADABLE":
        return _not_evaluated(
            "INSUFFICIENT_DATA",
            "UNGRADABLE readings cannot be interpreted.",
            quality,
        )

    current_values = {}

    for feature in FEATURES:
        value = _finite_number(
            getattr(reading, feature, None)
        )

        if value is None:
            return _not_evaluated(
                "INVALID_FEATURES",
                "A required current telemetry feature "
                "is missing or invalid.",
                quality,
            )

        current_values[feature] = value

    astronaut_id = getattr(
        reading,
        "astronaut_id",
        None,
    )

    recorded_at = getattr(
        reading,
        "recorded_at",
        None,
    )

    if astronaut_id is None or recorded_at is None:
        return _not_evaluated(
            "INVALID_READING",
            "Astronaut identity or reading timestamp is missing.",
            quality,
        )

    if timezone.is_naive(recorded_at):
        return _not_evaluated(
            "INVALID_READING",
            "Reading timestamp must be timezone-aware.",
            quality,
        )

    cutoff = recorded_at - timedelta(
        days=BASELINE_WINDOW_DAYS
    )

    eligible = []

    for historical in historical_readings:

        if getattr(historical, "astronaut_id", None) != astronaut_id:
            continue

        if not bool(
            getattr(historical, "is_synthetic", False)
        ):
            continue

        historical_quality = str(
            getattr(historical, "data_quality", "")
        ).split(".")[-1].upper()

        if historical_quality != "VALID":
            continue

        historical_time = getattr(
            historical,
            "recorded_at",
            None,
        )

        if historical_time is None:
            continue

        if timezone.is_naive(historical_time):
            continue

        # Exclude current and future readings.
        if historical_time >= recorded_at:
            continue

        if historical_time < cutoff:
            continue

        eligible.append(historical)

    eligible.sort(
        key=lambda item: item.recorded_at,
        reverse=True,
    )

    eligible = eligible[:MAX_BASELINE_READINGS]

    if len(eligible) < MIN_BASELINE_READINGS:
        result = _not_evaluated(
            "INSUFFICIENT_DATA",
            (
                f"Only {len(eligible)} eligible historical "
                f"readings are available. At least "
                f"{MIN_BASELINE_READINGS} are required."
            ),
            quality,
        )

        result["astronaut_id"] = astronaut_id
        result["baseline_readings"] = len(eligible)

        return result

    feature_results = {}

    for feature in FEATURES:

        historical_values = []

        for historical in eligible:
            value = _finite_number(
                getattr(historical, feature, None)
            )

            if value is None:
                return _not_evaluated(
                    "INVALID_FEATURES",
                    "Historical baseline contains an invalid "
                    "telemetry feature.",
                    quality,
                )

            historical_values.append(value)

        feature_results[feature] = _calculate_feature(
            current_values[feature],
            historical_values,
        )

    measurable = [
        item
        for item in feature_results.values()
        if item["deviation_detected"] is not None
    ]

    if not measurable:
        overall_status = "INSUFFICIENT_VARIABILITY"

    elif any(
        item["deviation_detected"]
        for item in measurable
    ):
        overall_status = "DEVIATION"

    else:
        overall_status = "WITHIN_BASELINE"

    if quality == "SUSPECT":
        explanation = (
            "Current reading has SUSPECT quality and requires "
            "human review. It was not used as a baseline sample."
        )
    else:
        explanation = (
            "Current synthetic reading was compared with the "
            "astronaut's preceding VALID synthetic readings."
        )

    return {
        "enabled": True,
        "status": overall_status,
        "astronaut_id": astronaut_id,
        "baseline_readings": len(eligible),
        "minimum_required": MIN_BASELINE_READINGS,
        "window_days": BASELINE_WINDOW_DAYS,
        "maximum_reference_readings": MAX_BASELINE_READINGS,
        "robust_z_threshold": ROBUST_Z_THRESHOLD,
        "data_quality": quality,
        "features": feature_results,
        "explanation": explanation,
        "clinical_validation": False,
        "disclaimer": (
            "Synthetic research demonstration only. "
            "Not a diagnosis, medical risk score, or "
            "treatment recommendation. Human review required."
        ),
    }


def get_personal_baseline(reading):
    """
    Retrieve eligible historical readings from the database
    and calculate the astronaut-specific baseline.
    """

    if not bool(getattr(reading, "is_synthetic", False)):
        return _not_evaluated(
            "NOT_EVALUATED",
            "Only synthetic readings are supported.",
        )

    quality = str(
        getattr(reading, "data_quality", "")
    ).split(".")[-1].upper()

    if quality == "UNGRADABLE":
        return _not_evaluated(
            "INSUFFICIENT_DATA",
            "UNGRADABLE readings cannot be interpreted.",
            quality,
        )

    if not getattr(reading, "astronaut_id", None):
        return _not_evaluated(
            "INVALID_READING",
            "Astronaut identity is missing.",
            quality,
        )

    recorded_at = getattr(
        reading,
        "recorded_at",
        None,
    )

    if recorded_at is None or timezone.is_naive(recorded_at):
        return _not_evaluated(
            "INVALID_READING",
            "A valid timezone-aware timestamp is required.",
            quality,
        )

    cutoff = recorded_at - timedelta(
        days=BASELINE_WINDOW_DAYS
    )

    historical = (
        VitalSignReading.objects
        .filter(
            astronaut_id=reading.astronaut_id,
            is_synthetic=True,
            data_quality=VitalSignReading.DataQuality.VALID,
            recorded_at__gte=cutoff,
            recorded_at__lt=recorded_at,
        )
        .order_by("-recorded_at", "-id")[
            :MAX_BASELINE_READINGS
        ]
    )

    return calculate_personal_baseline(
        reading,
        historical,
    )
