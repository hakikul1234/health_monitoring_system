"""
Isolation Forest anomaly detection engine.

This model learns patterns from synthetic normal telemetry.
It is an experimental software component and is not a
clinical diagnostic or astronaut fitness assessment tool.
"""

import numpy as np

from sklearn.ensemble import IsolationForest


class IsolationForestDetector:
    """
    Unsupervised anomaly detector for four telemetry features.

    Training uses normal-only synthetic samples.
    Validation calibrates an independent anomaly threshold.
    """

    def __init__(
        self,
        n_estimators=300,
        max_samples=256,
        random_state=42,
        target_false_positive_rate=0.05,
        n_jobs=-1,
    ):

        if n_estimators < 1:
            raise ValueError(
                "n_estimators must be at least 1."
            )

        if max_samples < 2:
            raise ValueError(
                "max_samples must be at least 2."
            )

        if not 0.0 < target_false_positive_rate < 1.0:
            raise ValueError(
                "target_false_positive_rate must be between 0 and 1."
            )

        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.random_state = random_state
        self.target_false_positive_rate = (
            target_false_positive_rate
        )
        self.n_jobs = n_jobs

        self.model = None
        self.anomaly_threshold = None
        self.is_fitted = False
        self.calibration_metadata = None

    @staticmethod
    def _validate_matrix(X, name):
        """Validate a numerical feature matrix."""

        matrix = np.asarray(
            X,
            dtype=np.float64
        )

        if matrix.ndim != 2:
            raise ValueError(
                f"{name} must be a two-dimensional matrix."
            )

        if matrix.shape[0] < 1:
            raise ValueError(
                f"{name} must contain at least one sample."
            )

        if matrix.shape[1] != 4:
            raise ValueError(
                f"{name} must contain exactly four features."
            )

        if not np.isfinite(matrix).all():
            raise ValueError(
                f"{name} contains non-finite values."
            )

        return matrix

    def fit(self, X_train, X_validation):
        """
        Train on normal-only samples and calibrate threshold.

        The validation matrix must be independently generated
        normal-only telemetry.
        """

        train = self._validate_matrix(
            X_train,
            "X_train"
        )

        validation = self._validate_matrix(
            X_validation,
            "X_validation"
        )

        if train.shape[0] < 2:
            raise ValueError(
                "At least two training samples are required."
            )

        effective_max_samples = min(
            self.max_samples,
            train.shape[0]
        )

        self.model = IsolationForest(
            n_estimators=self.n_estimators,
            max_samples=effective_max_samples,
            contamination="auto",
            random_state=self.random_state,
            n_jobs=self.n_jobs,
        )

        self.model.fit(train)

        # Lower sklearn score_samples means more anomalous.
        # Negation creates an intuitive higher-is-more-anomalous score.
        validation_scores = -self.model.score_samples(
            validation
        )

        # Calibrate threshold using only independent normal validation.
        self.anomaly_threshold = float(
            np.quantile(
                validation_scores,
                1.0 - self.target_false_positive_rate,
            )
        )

        self.is_fitted = True

        self.calibration_metadata = {
            "validation_samples": int(
                validation.shape[0]
            ),
            "target_false_positive_rate": (
                self.target_false_positive_rate
            ),
            "anomaly_threshold": self.anomaly_threshold,
            "calibration_data": "SYNTHETIC_NORMAL_ONLY",
        }

        return self.calibration_metadata

    def predict_batch(self, X):
        """Predict anomaly scores for a batch of readings."""

        if not self.is_fitted:
            raise RuntimeError(
                "Model must be trained and calibrated before prediction."
            )

        matrix = self._validate_matrix(
            X,
            "X"
        )

        anomaly_scores = -self.model.score_samples(
            matrix
        )

        predictions = (
            anomaly_scores > self.anomaly_threshold
        ).astype(np.int64)

        return {
            "anomaly_scores": anomaly_scores,
            "predictions": predictions,
            "threshold": self.anomaly_threshold,
        }

    def predict_one(self, feature_vector):
        """Predict one telemetry feature vector."""

        vector = np.asarray(
            feature_vector,
            dtype=np.float64
        )

        if vector.ndim == 1:
            vector = vector.reshape(1, -1)

        result = self.predict_batch(vector)

        return {
            "anomaly_score": float(
                result["anomaly_scores"][0]
            ),
            "is_anomalous": bool(
                result["predictions"][0]
            ),
            "threshold": self.anomaly_threshold,
            "model_type": "ISOLATION_FOREST",
        }
