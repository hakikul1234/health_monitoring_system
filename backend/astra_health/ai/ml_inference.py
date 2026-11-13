"""
ML inference service for ASTRA-PULSE AI.

Uses the locally trained Isolation Forest model.

Important:
- Only synthetic telemetry is supported.
- UNGRADABLE readings are never interpreted.
- Anomaly scores are not probabilities or medical risk scores.
- This service is a research software demonstration.
"""

from functools import lru_cache

from astra_health.ai.feature_engineering import (
    extract_feature_vector,
    get_reading_quality,
)

from astra_health.ai.model_registry import load_detector


MODEL_VERSION = "v1.0.0"


@lru_cache(maxsize=1)
def _load_cached_model():
    """
    Load the trusted model once and reuse it.

    The cache avoids loading the Joblib artifact for
    every incoming health reading.
    """

    return load_detector(MODEL_VERSION)


def clear_model_cache():
    """
    Clear the cached model.

    Useful when explicitly switching model versions
    or running isolated tests.
    """

    _load_cached_model.cache_clear()


def _not_evaluated(status, explanation, quality=None):
    """Build a consistent response for skipped inference."""

    return {
        "enabled": True,
        "status": status,
        "is_anomalous": None,
        "anomaly_score": None,
        "threshold": None,
        "model_type": "ISOLATION_FOREST",
        "model_version": MODEL_VERSION,
        "data_quality": quality,
        "explanation": explanation,
        "score_interpretation": (
            "Anomaly score is not a probability, "
            "medical risk score, or diagnosis."
        ),
        "clinical_validation": False,
    }


def run_ml_inference(reading):
    """
    Execute ML inference for one supported synthetic reading.

    Expected input:
        VitalSignReading model instance.

    Returns:
        Structured ML inference result.
    """

    # --------------------------------------------------
    # 1. SYNTHETIC DATA SAFETY GATE
    # --------------------------------------------------

    if not bool(getattr(reading, "is_synthetic", False)):

        return _not_evaluated(
            status="NOT_EVALUATED",
            explanation=(
                "ML inference is restricted to synthetic "
                "demonstration telemetry. Non-synthetic "
                "readings are not evaluated."
            ),
        )

    # --------------------------------------------------
    # 2. DATA QUALITY GATE
    # --------------------------------------------------

    try:
        quality = get_reading_quality(reading)

    except (ValueError, TypeError, AttributeError):

        return _not_evaluated(
            status="INSUFFICIENT_DATA",
            explanation=(
                "Data quality information is missing "
                "or invalid."
            ),
        )

    if quality == "UNGRADABLE":

        return _not_evaluated(
            status="INSUFFICIENT_DATA",
            quality=quality,
            explanation=(
                "Reading is UNGRADABLE. Placeholder values "
                "must not be interpreted by the ML model."
            ),
        )

    # --------------------------------------------------
    # 3. FEATURE EXTRACTION
    # --------------------------------------------------

    try:
        feature_vector = extract_feature_vector(reading)

    except (ValueError, TypeError, AttributeError) as exc:

        return _not_evaluated(
            status="INVALID_FEATURES",
            quality=quality,
            explanation=str(exc),
        )

    # --------------------------------------------------
    # 4. LAZY MODEL LOADING
    # --------------------------------------------------

    try:
        detector, metadata = _load_cached_model()

    except Exception as exc:

        return {
            **_not_evaluated(
                status="MODEL_UNAVAILABLE",
                quality=quality,
                explanation=(
                    "The trained ML model could not be loaded. "
                    "Rule-based analysis can continue independently."
                ),
            ),
            "error_type": type(exc).__name__,
        }

    # --------------------------------------------------
    # 5. ML PREDICTION
    # --------------------------------------------------

    try:
        prediction = detector.predict_one(
            feature_vector
        )

    except Exception as exc:

        return {
            **_not_evaluated(
                status="INFERENCE_FAILED",
                quality=quality,
                explanation=(
                    "ML inference failed. "
                    "Rule-based analysis can continue independently."
                ),
            ),
            "error_type": type(exc).__name__,
        }

    is_anomalous = bool(
        prediction["is_anomalous"]
    )

    anomaly_score = float(
        prediction["anomaly_score"]
    )

    threshold = float(
        prediction["threshold"]
    )

    # --------------------------------------------------
    # 6. BUILD EXPLAINABLE ML RESULT
    # --------------------------------------------------

    if is_anomalous:

        explanation = (
            "The Isolation Forest model identified this "
            "synthetic reading as an anomaly relative to "
            "its learned synthetic normal-data patterns."
        )

    else:

        explanation = (
            "The Isolation Forest model did not identify "
            "this synthetic reading as an anomaly relative "
            "to its learned synthetic normal-data patterns."
        )

    if quality == "SUSPECT":

        explanation += (
            " The reading has SUSPECT data quality and "
            "requires human review."
        )

    return {
        "enabled": True,
        "status": (
            "ANOMALY" if is_anomalous else "NORMAL"
        ),
        "is_anomalous": is_anomalous,
        "anomaly_score": anomaly_score,
        "threshold": threshold,
        "model_type": "ISOLATION_FOREST",
        "model_version": metadata["model_version"],
        "data_quality": quality,
        "explanation": explanation,
        "score_interpretation": (
            "Higher scores indicate greater deviation from "
            "the model's learned synthetic normal-data patterns. "
            "This score is not a probability or medical risk score."
        ),
        "clinical_validation": False,
    }
