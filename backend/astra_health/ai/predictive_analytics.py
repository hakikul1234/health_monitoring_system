"""
Timestamp-based predictive trend analytics for ASTRA-PULSE AI.

Research prototype using synthetic VALID telemetry only.
Predictions are trend estimates, not medical forecasts.
"""

import math
from datetime import timedelta

import numpy as np
from django.utils import timezone

from astra_health.models import VitalSignReading


FEATURES = (
    "heart_rate_bpm",
    "spo2_percent",
    "body_temperature_c",
    "respiratory_rate_bpm",
)

MIN_HISTORY_READINGS = 10
MIN_HISTORY_SPAN_SECONDS = 300
MAX_HISTORY_READINGS = 100
HISTORY_WINDOW_DAYS = 30
FORECAST_HORIZON_SECONDS = 300


def _empty_result(status, explanation, quality=None):
    return {
        "enabled": True,
        "status": status,
        "algorithm": "TIMESTAMP_LINEAR_REGRESSION",
        "model_version": "trend-v1.0.0",
        "astronaut_id": None,
        "historical_readings": 0,
        "minimum_required": MIN_HISTORY_READINGS,
        "history_span_seconds": 0,
        "forecast_horizon_seconds": FORECAST_HORIZON_SECONDS,
        "data_quality": quality,
        "features": {},
        "clinical_validation": False,
        "explanation": explanation,
        "disclaimer": (
            "Synthetic research demonstration only. "
            "Not a diagnosis, medical risk score, or clinical forecast. "
            "Human review is required."
        ),
    }


def _finite_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    return number if math.isfinite(number) else None


def _calculate_trend(times, values):
    """
    Fit a linear trend using elapsed seconds from first sample.
    """

    x = np.asarray(times, dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)

    if len(x) < MIN_HISTORY_READINGS:
        return None

    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        return None

    span = float(x[-1] - x[0])

    if span < MIN_HISTORY_SPAN_SECONDS:
        return None

    centered_x = x - x.mean()
    centered_y = y - y.mean()

    denominator = float(np.dot(centered_x, centered_x))

    if denominator <= 0:
        return None

    slope = float(
        np.dot(centered_x, centered_y) / denominator
    )

    intercept = float(y.mean() - slope * x.mean())

    forecast_time = float(x[-1] + FORECAST_HORIZON_SECONDS)

    predicted = intercept + slope * forecast_time

    fitted = intercept + slope * x

    residuals = y - fitted

    rmse = float(
        np.sqrt(np.mean(np.square(residuals)))
    )

    if abs(slope) < 1e-9:
        direction = "STABLE"
    elif slope > 0:
        direction = "INCREASING"
    else:
        direction = "DECREASING"

    return {
        "latest_value": round(float(y[-1]), 4),
        "predicted_value": round(float(predicted), 4),
        "slope_per_minute": round(slope * 60.0, 6),
        "trend_direction": direction,
        "regression_rmse": round(rmse, 4),
        "observed_change": round(
            float(y[-1] - y[0]), 4
        ),
        "explanation": (
            "A timestamp-based linear trend was fitted to "
            "historical VALID synthetic readings. The estimate "
            "extends this observed trend by five minutes."
        ),
    }


def calculate_predictive_analytics(reading, historical_readings):
    """
    Calculate astronaut-specific trend estimates.

    Historical samples must be earlier than the current reading.
    """

    if not bool(getattr(reading, "is_synthetic", False)):
        return _empty_result(
            "NOT_EVALUATED",
            "Only synthetic telemetry is supported.",
        )

    quality = str(
        getattr(reading, "data_quality", "")
    ).split(".")[-1].upper()

    if quality != "VALID":
        return _empty_result(
            "INSUFFICIENT_DATA",
            "Current reading must have VALID data quality.",
            quality,
        )

    astronaut_id = getattr(reading, "astronaut_id", None)
    recorded_at = getattr(reading, "recorded_at", None)

    if astronaut_id is None or recorded_at is None:
        return _empty_result(
            "INVALID_READING",
            "Astronaut identity or timestamp is missing.",
            quality,
        )

    if timezone.is_naive(recorded_at):
        return _empty_result(
            "INVALID_READING",
            "A timezone-aware timestamp is required.",
            quality,
        )

    current_values = {}

    for feature in FEATURES:
        value = _finite_number(
            getattr(reading, feature, None)
        )

        if value is None:
            return _empty_result(
                "INVALID_FEATURES",
                "Current telemetry contains an invalid feature.",
                quality,
            )

        current_values[feature] = value

    cutoff = recorded_at - timedelta(
        days=HISTORY_WINDOW_DAYS
    )

    eligible = []

    for historical in historical_readings:

        if getattr(historical, "astronaut_id", None) != astronaut_id:
            continue

        if not bool(getattr(historical, "is_synthetic", False)):
            continue

        historical_quality = str(
            getattr(historical, "data_quality", "")
        ).split(".")[-1].upper()

        if historical_quality != "VALID":
            continue

        historical_time = getattr(
            historical, "recorded_at", None
        )

        if historical_time is None or timezone.is_naive(historical_time):
            continue

        if historical_time >= recorded_at or historical_time < cutoff:
            continue

        eligible.append(historical)

    eligible.sort(
        key=lambda item: (item.recorded_at, getattr(item, "id", 0) or 0)
    )

    eligible = eligible[-MAX_HISTORY_READINGS:]

    if len(eligible) < MIN_HISTORY_READINGS:
        result = _empty_result(
            "INSUFFICIENT_DATA",
            (
                f"Only {len(eligible)} eligible historical readings "
                f"are available. At least {MIN_HISTORY_READINGS} "
                "are required."
            ),
            quality,
        )

        result["astronaut_id"] = astronaut_id
        result["historical_readings"] = len(eligible)

        return result

    first_time = eligible[0].recorded_at
    last_time = eligible[-1].recorded_at

    span_seconds = (
        last_time - first_time
    ).total_seconds()

    if span_seconds < MIN_HISTORY_SPAN_SECONDS:
        result = _empty_result(
            "INSUFFICIENT_DATA",
            "Historical readings must span at least five minutes.",
            quality,
        )

        result["astronaut_id"] = astronaut_id
        result["historical_readings"] = len(eligible)
        result["history_span_seconds"] = round(span_seconds, 2)

        return result

    origin = first_time

    times = [
        (item.recorded_at - origin).total_seconds()
        for item in eligible
    ]

    feature_results = {}

    for feature in FEATURES:

        values = []

        for historical in eligible:
            value = _finite_number(
                getattr(historical, feature, None)
            )

            if value is None:
                return _empty_result(
                    "INVALID_FEATURES",
                    "Historical telemetry contains an invalid feature.",
                    quality,
                )

            values.append(value)

        trend = _calculate_trend(times, values)

        if trend is None:
            return _empty_result(
                "INSUFFICIENT_DATA",
                "A reliable time-based trend could not be fitted.",
                quality,
            )

        feature_results[feature] = trend

    return {
        "enabled": True,
        "status": "TREND_ESTIMATED",
        "algorithm": "TIMESTAMP_LINEAR_REGRESSION",
        "model_version": "trend-v1.0.0",
        "astronaut_id": astronaut_id,
        "historical_readings": len(eligible),
        "minimum_required": MIN_HISTORY_READINGS,
        "history_span_seconds": round(span_seconds, 2),
        "forecast_horizon_seconds": FORECAST_HORIZON_SECONDS,
        "data_quality": quality,
        "features": feature_results,
        "clinical_validation": False,
        "explanation": (
            "Feature-wise trends were estimated using the "
            "astronaut's preceding VALID synthetic readings."
        ),
        "disclaimer": (
            "Synthetic research demonstration only. "
            "Not a diagnosis, medical risk score, or clinical forecast. "
            "Human review is required."
        ),
    }


def get_predictive_analytics(reading):
    """
    Retrieve eligible history from the database and estimate trends.
    """

    if not bool(getattr(reading, "is_synthetic", False)):
        return _empty_result(
            "NOT_EVALUATED",
            "Only synthetic telemetry is supported.",
        )

    quality = str(
        getattr(reading, "data_quality", "")
    ).split(".")[-1].upper()

    if quality != "VALID":
        return _empty_result(
            "INSUFFICIENT_DATA",
            "Current reading must have VALID data quality.",
            quality,
        )

    if not getattr(reading, "astronaut_id", None):
        return _empty_result(
            "INVALID_READING",
            "Astronaut identity is missing.",
            quality,
        )

    recorded_at = getattr(reading, "recorded_at", None)

    if recorded_at is None or timezone.is_naive(recorded_at):
        return _empty_result(
            "INVALID_READING",
            "A timezone-aware timestamp is required.",
            quality,
        )

    cutoff = recorded_at - timedelta(
        days=HISTORY_WINDOW_DAYS
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
            :MAX_HISTORY_READINGS
        ]
    )

    return calculate_predictive_analytics(
        reading,
        historical,
    )
