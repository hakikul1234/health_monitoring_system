"""
Feature engineering for ASTRA-PULSE AI.

This module converts synthetic astronaut telemetry into
a consistent numerical feature vector for ML inference.

This is a research software demonstration, not a
medical diagnostic system.
"""

import math

import numpy as np


FEATURE_NAMES = (
    "heart_rate_bpm",
    "spo2_percent",
    "body_temperature_c",
    "respiratory_rate_bpm",
)

FEATURE_COUNT = len(FEATURE_NAMES)


def _get_value(reading, field):
    """Read a feature from either a dictionary or model instance."""

    if isinstance(reading, dict):
        if field not in reading:
            raise ValueError(
                f"Missing telemetry feature: {field}"
            )

        return reading[field]

    if not hasattr(reading, field):
        raise ValueError(
            f"Reading does not contain feature: {field}"
        )

    return getattr(reading, field)


def get_reading_quality(reading):
    """Return normalized data quality."""

    quality = _get_value(reading, "data_quality")

    return str(quality).split(".")[-1].upper()


def extract_feature_vector(reading):
    """
    Convert one telemetry reading into a numerical vector.

    UNGRADABLE readings are rejected because their values
    are placeholders and must never be interpreted.
    """

    quality = get_reading_quality(reading)

    if quality == "UNGRADABLE":
        raise ValueError(
            "UNGRADABLE telemetry cannot be used for ML inference."
        )

    values = []

    for feature_name in FEATURE_NAMES:

        raw_value = _get_value(
            reading,
            feature_name
        )

        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            raise ValueError(
                f"Invalid numerical feature: {feature_name}"
            )

        if not math.isfinite(value):
            raise ValueError(
                f"Non-finite feature value: {feature_name}"
            )

        values.append(value)

    vector = np.asarray(
        values,
        dtype=np.float64
    )

    if vector.shape != (FEATURE_COUNT,):
        raise ValueError(
            "Unexpected telemetry feature vector shape."
        )

    return vector


def extract_feature_matrix(readings):
    """
    Convert multiple readings into a 2D feature matrix.
    """

    vectors = [
        extract_feature_vector(reading)
        for reading in readings
    ]

    if not vectors:
        raise ValueError(
            "At least one valid telemetry reading is required."
        )

    return np.vstack(vectors)
