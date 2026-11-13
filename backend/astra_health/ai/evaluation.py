"""
Evaluation metrics for ASTRA-PULSE AI anomaly detection.

Metrics are calculated on independent synthetic test data.
They must not be interpreted as clinical performance.
"""

import numpy as np

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    average_precision_score,
    roc_auc_score,
)


def evaluate_detector(
    y_true,
    anomaly_scores,
    threshold,
    scenarios=None,
):
    """Evaluate binary anomaly predictions and scenario behavior."""

    y_true = np.asarray(y_true, dtype=np.int64)
    scores = np.asarray(anomaly_scores, dtype=np.float64)

    if y_true.ndim != 1 or scores.ndim != 1:
        raise ValueError("Labels and scores must be one-dimensional.")

    if len(y_true) == 0 or len(y_true) != len(scores):
        raise ValueError("Labels and scores must have equal non-zero lengths.")

    if not np.isin(y_true, [0, 1]).all():
        raise ValueError("Labels must contain only 0 and 1.")

    if not np.isfinite(scores).all():
        raise ValueError("Anomaly scores contain non-finite values.")

    if not np.isfinite(threshold):
        raise ValueError("Threshold must be finite.")

    if len(np.unique(y_true)) != 2:
        raise ValueError("Evaluation requires both normal and anomaly labels.")

    y_pred = (scores > float(threshold)).astype(np.int64)

    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    )

    tn, fp, fn, tp = matrix.ravel()

    metrics = {
        "sample_count": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(
            balanced_accuracy_score(y_true, y_pred)
        ),
        "precision": float(
            precision_score(y_true, y_pred, zero_division=0)
        ),
        "recall": float(
            recall_score(y_true, y_pred, zero_division=0)
        ),
        "f1_score": float(
            f1_score(y_true, y_pred, zero_division=0)
        ),
        "pr_auc_average_precision": float(
            average_precision_score(y_true, scores)
        ),
        "roc_auc": float(
            roc_auc_score(y_true, scores)
        ),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
        "threshold": float(threshold),
        "evaluation_data": "SYNTHETIC_TEST_DATA",
        "clinical_validation": False,
    }

    scenario_metrics = {}

    if scenarios is not None:

        scenarios = np.asarray(scenarios, dtype=object)

        if scenarios.ndim != 1 or len(scenarios) != len(y_true):
            raise ValueError(
                "Scenario labels must match the test sample count."
            )

        for scenario in sorted(set(scenarios.tolist())):

            mask = scenarios == scenario

            scenario_metrics[str(scenario)] = {
                "sample_count": int(mask.sum()),
                "expected_label": int(y_true[mask][0]),
                "anomaly_detection_rate": float(
                    y_pred[mask].mean()
                ),
                "predicted_anomalies": int(y_pred[mask].sum()),
            }

    return {
        "metrics": metrics,
        "scenario_metrics": scenario_metrics,
    }
