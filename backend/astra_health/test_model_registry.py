import json
import tempfile
import unittest

from pathlib import Path
from unittest.mock import patch

import numpy as np

from astra_health.ai import model_registry
from astra_health.ai.isolation_forest import IsolationForestDetector


class ModelRegistryTests(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()

        self.registry_patch = patch.object(
            model_registry,
            "ARTIFACT_ROOT",
            Path(self.temp_directory.name),
        )

        self.registry_patch.start()

        rng = np.random.default_rng(42)

        X_train = rng.normal(
            loc=0.0,
            scale=1.0,
            size=(100, 4),
        )

        X_validation = rng.normal(
            loc=0.0,
            scale=1.0,
            size=(50, 4),
        )

        self.detector = IsolationForestDetector(
            n_estimators=50,
            max_samples=64,
            random_state=42,
            n_jobs=1,
        )

        self.detector.fit(
            X_train,
            X_validation,
        )

        self.X_test = rng.normal(
            loc=0.0,
            scale=1.0,
            size=(20, 4),
        )

    def tearDown(self):
        self.registry_patch.stop()
        self.temp_directory.cleanup()

    def test_save_and_load_preserves_predictions(self):

        original = self.detector.predict_batch(
            self.X_test
        )

        model_registry.save_detector(
            self.detector,
            "v1.0.0",
            {"test": True},
        )

        loaded, metadata = model_registry.load_detector(
            "v1.0.0"
        )

        restored = loaded.predict_batch(
            self.X_test
        )

        np.testing.assert_array_equal(
            original["predictions"],
            restored["predictions"],
        )

        np.testing.assert_allclose(
            original["anomaly_scores"],
            restored["anomaly_scores"],
        )

        self.assertFalse(
            metadata["clinical_validation"]
        )

    def test_duplicate_model_version_is_rejected(self):

        model_registry.save_detector(
            self.detector,
            "v1.0.0",
        )

        with self.assertRaises(FileExistsError):

            model_registry.save_detector(
                self.detector,
                "v1.0.0",
            )

    def test_invalid_version_is_rejected(self):

        with self.assertRaises(ValueError):

            model_registry.save_detector(
                self.detector,
                "invalid-version",
            )

        with self.assertRaises(ValueError):

            model_registry.load_detector(
                "../v1.0.0",
            )

    def test_checksum_tampering_is_detected(self):

        saved = model_registry.save_detector(
            self.detector,
            "v1.0.0",
        )

        artifact_path = Path(
            saved["artifact_path"]
        )

        with open(
            artifact_path,
            "ab",
        ) as file:

            file.write(b"tampered-data")

        with self.assertRaisesRegex(
            ValueError,
            "SHA-256",
        ):

            model_registry.load_detector(
                "v1.0.0",
            )

    def test_incompatible_feature_schema_is_rejected(self):

        saved = model_registry.save_detector(
            self.detector,
            "v1.0.0",
        )

        metadata_path = Path(
            saved["metadata_path"]
        )

        with open(
            metadata_path,
            "r",
            encoding="utf-8",
        ) as file:

            metadata = json.load(file)

        metadata["feature_names"] = [
            "incorrect_feature"
        ]

        with open(
            metadata_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                metadata,
                file,
                indent=4,
            )

        with self.assertRaisesRegex(
            ValueError,
            "feature schema",
        ):

            model_registry.load_detector(
                "v1.0.0",
            )

    def test_missing_metadata_is_rejected(self):

        model_registry.save_detector(
            self.detector,
            "v1.0.0",
        )

        metadata_path = (
            model_registry.ARTIFACT_ROOT
            / "isolation_forest_v1.0.0.json"
        )

        metadata_path.unlink()

        with self.assertRaises(FileNotFoundError):

            model_registry.load_detector(
                "v1.0.0",
            )


if __name__ == "__main__":
    unittest.main()
