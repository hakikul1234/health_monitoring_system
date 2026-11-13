"""
Versioned model artifact registry for ASTRA-PULSE AI.

Only trusted locally generated Joblib artifacts should be loaded.
SHA-256 verifies artifact integrity against its metadata.
"""

import hashlib
import json
import re

from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn

from astra_health.ai.feature_engineering import FEATURE_NAMES
from astra_health.ai.isolation_forest import IsolationForestDetector


ARTIFACT_ROOT = (
    Path(__file__).resolve().parents[2]
    / "ml_artifacts"
    / "isolation_forest"
)

VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+$")


def _validate_version(version):
    if not isinstance(version, str):
        raise ValueError("Model version must be a string.")

    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError(
            "Invalid model version. Expected format: v1.0.0"
        )


def _calculate_sha256(file_path):
    digest = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def save_detector(
    detector,
    model_version,
    training_metadata=None,
):
    """
    Save a trained detector and its metadata.

    Existing version files are never overwritten.
    """

    _validate_version(model_version)

    if not isinstance(detector, IsolationForestDetector):
        raise TypeError(
            "Only IsolationForestDetector instances can be saved."
        )

    if not detector.is_fitted or detector.model is None:
        raise ValueError(
            "Cannot save an untrained detector."
        )

    if detector.anomaly_threshold is None:
        raise ValueError(
            "Cannot save a detector without a calibrated threshold."
        )

    ARTIFACT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    artifact_name = (
        f"isolation_forest_{model_version}.joblib"
    )

    metadata_name = (
        f"isolation_forest_{model_version}.json"
    )

    artifact_path = ARTIFACT_ROOT / artifact_name
    metadata_path = ARTIFACT_ROOT / metadata_name

    if artifact_path.exists() or metadata_path.exists():
        raise FileExistsError(
            f"Model version {model_version} already exists. "
            "Create a new version instead of overwriting it."
        )

    temporary_artifact = ARTIFACT_ROOT / (
        artifact_name + ".tmp"
    )

    temporary_metadata = ARTIFACT_ROOT / (
        metadata_name + ".tmp"
    )

    try:
        joblib.dump(
            detector,
            temporary_artifact,
            compress=3,
        )

        checksum = _calculate_sha256(
            temporary_artifact
        )

        metadata = {
            "model_name": "ASTRA-PULSE Isolation Forest",
            "model_type": "ISOLATION_FOREST",
            "model_version": model_version,
            "artifact_filename": artifact_name,
            "artifact_sha256": checksum,
            "feature_names": list(FEATURE_NAMES),
            "feature_count": len(FEATURE_NAMES),
            "anomaly_threshold": float(
                detector.anomaly_threshold
            ),
            "n_estimators": detector.n_estimators,
            "max_samples": detector.max_samples,
            "random_state": detector.random_state,
            "target_false_positive_rate": (
                detector.target_false_positive_rate
            ),
            "calibration": detector.calibration_metadata,
            "training_metadata": training_metadata or {},
            "numpy_version": np.__version__,
            "scikit_learn_version": sklearn.__version__,
            "joblib_version": joblib.__version__,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "data_type": "SYNTHETIC",
            "clinical_validation": False,
        }

        with open(
            temporary_metadata,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                metadata,
                file,
                indent=4,
                sort_keys=True,
            )

        temporary_artifact.replace(
            artifact_path
        )

        temporary_metadata.replace(
            metadata_path
        )

    finally:
        if temporary_artifact.exists():
            temporary_artifact.unlink()

        if temporary_metadata.exists():
            temporary_metadata.unlink()

    return {
        "artifact_path": str(artifact_path),
        "metadata_path": str(metadata_path),
        "sha256": checksum,
        "model_version": model_version,
    }


def load_detector(model_version):
    """
    Load a trusted model after verifying metadata and checksum.
    """

    _validate_version(model_version)

    artifact_name = (
        f"isolation_forest_{model_version}.joblib"
    )

    metadata_name = (
        f"isolation_forest_{model_version}.json"
    )

    artifact_path = ARTIFACT_ROOT / artifact_name
    metadata_path = ARTIFACT_ROOT / metadata_name

    if not artifact_path.is_file():
        raise FileNotFoundError(
            f"Model artifact not found: {artifact_name}"
        )

    if not metadata_path.is_file():
        raise FileNotFoundError(
            f"Model metadata not found: {metadata_name}"
        )

    with open(
        metadata_path,
        "r",
        encoding="utf-8",
    ) as file:

        metadata = json.load(file)

    if metadata.get("model_version") != model_version:
        raise ValueError(
            "Model version does not match metadata."
        )

    if metadata.get("artifact_filename") != artifact_name:
        raise ValueError(
            "Artifact filename does not match metadata."
        )

    if metadata.get("feature_names") != list(FEATURE_NAMES):
        raise ValueError(
            "Saved model feature schema is incompatible."
        )

    if metadata.get("model_type") != "ISOLATION_FOREST":
        raise ValueError(
            "Unsupported model type."
        )

    expected_checksum = metadata.get("artifact_sha256")

    if not isinstance(expected_checksum, str):
        raise ValueError(
            "Artifact checksum is missing."
        )

    actual_checksum = _calculate_sha256(
        artifact_path
    )

    if actual_checksum != expected_checksum:
        raise ValueError(
            "Artifact SHA-256 verification failed."
        )

    # Only load artifacts generated and trusted by this project.
    detector = joblib.load(artifact_path)

    if not isinstance(detector, IsolationForestDetector):
        raise TypeError(
            "Loaded artifact is not an IsolationForestDetector."
        )

    if not detector.is_fitted or detector.model is None:
        raise ValueError(
            "Loaded model is not fitted."
        )

    if detector.anomaly_threshold is None:
        raise ValueError(
            "Loaded model has no calibrated threshold."
        )

    if float(metadata["anomaly_threshold"]) != float(
        detector.anomaly_threshold
    ):
        raise ValueError(
            "Model threshold does not match metadata."
        )

    return detector, metadata
