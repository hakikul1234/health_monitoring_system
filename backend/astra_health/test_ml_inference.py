from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from astra_health.ai.ml_inference import (
    run_ml_inference,
    clear_model_cache,
    _load_cached_model,
)


class MLInferenceTests(SimpleTestCase):

    def setUp(self):
        clear_model_cache()

    def tearDown(self):
        clear_model_cache()

    @staticmethod
    def make_reading(**overrides):

        values = {
            "is_synthetic": True,
            "data_quality": "VALID",
            "heart_rate_bpm": 75,
            "spo2_percent": 98,
            "body_temperature_c": 36.7,
            "respiratory_rate_bpm": 15,
        }

        values.update(overrides)

        return SimpleNamespace(**values)

    def test_normal_synthetic_reading_is_evaluated(self):

        reading = self.make_reading()

        result = run_ml_inference(reading)

        self.assertIn(
            result["status"],
            ["NORMAL", "ANOMALY"],
        )

        self.assertEqual(
            result["model_version"],
            "v1.0.0",
        )

        self.assertIsInstance(
            result["anomaly_score"],
            float,
        )

    def test_emergency_like_reading_is_detected(self):

        reading = self.make_reading(
            data_quality="SUSPECT",
            heart_rate_bpm=170,
            spo2_percent=82,
            body_temperature_c=39.2,
            respiratory_rate_bpm=35,
        )

        result = run_ml_inference(reading)

        self.assertEqual(
            result["status"],
            "ANOMALY",
        )

        self.assertTrue(
            result["is_anomalous"]
        )

        self.assertEqual(
            result["data_quality"],
            "SUSPECT",
        )

    def test_ungradable_reading_is_not_interpreted(self):

        reading = self.make_reading(
            data_quality="UNGRADABLE",
            heart_rate_bpm=170,
            spo2_percent=82,
            body_temperature_c=39.2,
            respiratory_rate_bpm=35,
        )

        result = run_ml_inference(reading)

        self.assertEqual(
            result["status"],
            "INSUFFICIENT_DATA",
        )

        self.assertIsNone(
            result["anomaly_score"]
        )

        self.assertIsNone(
            result["is_anomalous"]
        )

    def test_non_synthetic_reading_is_not_evaluated(self):

        reading = self.make_reading(
            is_synthetic=False,
        )

        result = run_ml_inference(reading)

        self.assertEqual(
            result["status"],
            "NOT_EVALUATED",
        )

        self.assertIsNone(
            result["anomaly_score"]
        )

    def test_missing_feature_is_rejected(self):

        reading = SimpleNamespace(
            is_synthetic=True,
            data_quality="VALID",
            spo2_percent=98,
            body_temperature_c=36.7,
            respiratory_rate_bpm=15,
        )

        result = run_ml_inference(reading)

        self.assertEqual(
            result["status"],
            "INVALID_FEATURES",
        )

        self.assertIsNone(
            result["anomaly_score"]
        )

    def test_model_is_cached_between_predictions(self):

        reading = self.make_reading()

        first = run_ml_inference(reading)
        second = run_ml_inference(reading)

        cache_info = _load_cached_model.cache_info()

        self.assertEqual(
            first["model_version"],
            second["model_version"],
        )

        self.assertGreaterEqual(
            cache_info.hits,
            1,
        )

        self.assertEqual(
            cache_info.misses,
            1,
        )

    @patch(
        "astra_health.ai.ml_inference._load_cached_model",
        side_effect=OSError("Simulated model loading failure"),
    )
    def test_model_unavailable_does_not_crash(self, mocked_loader):

        reading = self.make_reading()

        result = run_ml_inference(reading)

        self.assertEqual(
            result["status"],
            "MODEL_UNAVAILABLE",
        )

        self.assertIsNone(
            result["anomaly_score"]
        )

        self.assertEqual(
            result["error_type"],
            "OSError",
        )

        mocked_loader.assert_called_once()
