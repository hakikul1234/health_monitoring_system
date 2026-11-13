"""
Synthetic dataset generation for ASTRA-PULSE AI.

Isolation Forest is trained only on synthetic NORMAL_MISSION
samples. Validation and testing datasets remain independent.

All generated data is synthetic and is not representative
of clinically validated astronaut health distributions.
"""

import numpy as np

from astra_simulator.services.health_simulator import (
    generate_vital_sign_values,
)

from astra_health.ai.feature_engineering import (
    extract_feature_vector,
)


def _validate_sample_count(name, value):
    """Validate requested dataset sample counts."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer.")

    if value < 1:
        raise ValueError(f"{name} must be at least 1.")


def _generate_scenario_samples(
    scenario,
    count,
    starting_seed,
):
    """Generate deterministic feature vectors for one scenario."""

    vectors = []

    for index in range(count):

        reading = generate_vital_sign_values(
            scenario=scenario,
            seed=starting_seed + index,
        )

        vector = extract_feature_vector(reading)

        vectors.append(vector)

    return np.vstack(vectors)


def generate_synthetic_dataset(
    n_train=2000,
    n_validation=500,
    n_test_per_scenario=500,
    seed=20261112,
):
    """
    Generate independent training, validation and testing data.

    Training:
        NORMAL_MISSION only.

    Validation:
        NORMAL_MISSION only.

    Testing:
        NORMAL_MISSION      -> label 0
        HEALTH_ANOMALY      -> label 1
        EMERGENCY_MISSION   -> label 1

    DATA_QUALITY_FAULT:
        Explicitly excluded because its values are placeholders.
    """

    _validate_sample_count("n_train", n_train)
    _validate_sample_count("n_validation", n_validation)
    _validate_sample_count(
        "n_test_per_scenario",
        n_test_per_scenario,
    )

    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer.")

    if seed < 0:
        raise ValueError("seed cannot be negative.")

    # Independent deterministic seed ranges.
    train_start = seed
    validation_start = seed + 100000
    test_normal_start = seed + 200000
    test_anomaly_start = seed + 300000
    test_emergency_start = seed + 400000

    # 1. Training data: normal samples only.
    X_train = _generate_scenario_samples(
        "NORMAL_MISSION",
        n_train,
        train_start,
    )

    # 2. Validation data: independent normal samples.
    X_validation = _generate_scenario_samples(
        "NORMAL_MISSION",
        n_validation,
        validation_start,
    )

    # 3. Testing data: independent scenario samples.
    X_test_normal = _generate_scenario_samples(
        "NORMAL_MISSION",
        n_test_per_scenario,
        test_normal_start,
    )

    X_test_anomaly = _generate_scenario_samples(
        "HEALTH_ANOMALY",
        n_test_per_scenario,
        test_anomaly_start,
    )

    X_test_emergency = _generate_scenario_samples(
        "EMERGENCY_MISSION",
        n_test_per_scenario,
        test_emergency_start,
    )

    X_test = np.vstack([
        X_test_normal,
        X_test_anomaly,
        X_test_emergency,
    ])

    # 0 = synthetic normal scenario.
    # 1 = synthetic abnormal demonstration scenario.
    y_test = np.concatenate([
        np.zeros(n_test_per_scenario, dtype=np.int64),
        np.ones(n_test_per_scenario, dtype=np.int64),
        np.ones(n_test_per_scenario, dtype=np.int64),
    ])

    test_scenarios = np.concatenate([
        np.full(
            n_test_per_scenario,
            "NORMAL_MISSION",
            dtype=object,
        ),
        np.full(
            n_test_per_scenario,
            "HEALTH_ANOMALY",
            dtype=object,
        ),
        np.full(
            n_test_per_scenario,
            "EMERGENCY_MISSION",
            dtype=object,
        ),
    ])

    return {
        "X_train": X_train,
        "X_validation": X_validation,
        "X_test": X_test,
        "y_test": y_test,
        "test_scenarios": test_scenarios,
        "metadata": {
            "seed": seed,
            "training_samples": len(X_train),
            "validation_samples": len(X_validation),
            "testing_samples": len(X_test),
            "testing_normal_samples": n_test_per_scenario,
            "testing_anomaly_samples": n_test_per_scenario,
            "testing_emergency_samples": n_test_per_scenario,
            "training_scenarios": ["NORMAL_MISSION"],
            "validation_scenarios": ["NORMAL_MISSION"],
            "testing_scenarios": [
                "NORMAL_MISSION",
                "HEALTH_ANOMALY",
                "EMERGENCY_MISSION",
            ],
            "excluded_scenarios": [
                "DATA_QUALITY_FAULT",
            ],
            "all_data_synthetic": True,
            "training_is_normal_only": True,
        },
    }
