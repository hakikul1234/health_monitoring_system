from datetime import timedelta
from types import SimpleNamespace

from django.test import SimpleTestCase
from django.utils import timezone

from astra_health.ai.predictive_analytics import (
    calculate_predictive_analytics,
)


def make_reading(
    astronaut_id=35,
    minutes_ago=0,
    quality="VALID",
    synthetic=True,
    heart_rate=75,
    spo2=98,
    temperature=36.7,
    respiratory_rate=15,
):
    return SimpleNamespace(
        astronaut_id=astronaut_id,
        recorded_at=timezone.now() - timedelta(minutes=minutes_ago),
        data_quality=quality,
        is_synthetic=synthetic,
        heart_rate_bpm=heart_rate,
        spo2_percent=spo2,
        body_temperature_c=temperature,
        respiratory_rate_bpm=respiratory_rate,
        id=minutes_ago,
    )


def make_history(count=12, astronaut_id=35):
    now = timezone.now()

    readings = []

    for index in range(count):
        variation = (index % 3) - 1

        readings.append(
            SimpleNamespace(
                astronaut_id=astronaut_id,
                recorded_at=now - timedelta(minutes=count - index),
                data_quality="VALID",
                is_synthetic=True,
                heart_rate_bpm=75 + variation,
                spo2_percent=98 + variation,
                body_temperature_c=36.7 + (variation * 0.1),
                respiratory_rate_bpm=15 + variation,
                id=index + 1,
            )
        )

    return readings


class PredictiveAnalyticsTests(SimpleTestCase):

    def setUp(self):
        self.current = make_reading()
        self.history = make_history()

    def test_valid_history_produces_trend_estimate(self):
        result = calculate_predictive_analytics(
            self.current,
            self.history,
        )

        self.assertEqual(result["status"], "TREND_ESTIMATED")
        self.assertEqual(result["historical_readings"], 12)
        self.assertEqual(result["forecast_horizon_seconds"], 300)
        self.assertEqual(
            result["algorithm"],
            "TIMESTAMP_LINEAR_REGRESSION",
        )
        self.assertFalse(result["clinical_validation"])

        for feature in (
            "heart_rate_bpm",
            "spo2_percent",
            "body_temperature_c",
            "respiratory_rate_bpm",
        ):
            self.assertIn(feature, result["features"])
            self.assertIn(
                "predicted_value",
                result["features"][feature],
            )

    def test_insufficient_history_is_rejected(self):
        result = calculate_predictive_analytics(
            self.current,
            make_history(count=5),
        )

        self.assertEqual(result["status"], "INSUFFICIENT_DATA")

    def test_different_astronaut_history_is_excluded(self):
        result = calculate_predictive_analytics(
            self.current,
            make_history(count=12, astronaut_id=999),
        )

        self.assertEqual(result["status"], "INSUFFICIENT_DATA")
        self.assertEqual(result["historical_readings"], 0)

    def test_non_synthetic_current_reading_is_not_evaluated(self):
        current = make_reading(synthetic=False)

        result = calculate_predictive_analytics(
            current,
            self.history,
        )

        self.assertEqual(result["status"], "NOT_EVALUATED")

    def test_ungradable_current_reading_is_rejected(self):
        current = make_reading(quality="UNGRADABLE")

        result = calculate_predictive_analytics(
            current,
            self.history,
        )

        self.assertEqual(result["status"], "INSUFFICIENT_DATA")

    def test_suspect_current_reading_is_rejected(self):
        current = make_reading(quality="SUSPECT")

        result = calculate_predictive_analytics(
            current,
            self.history,
        )

        self.assertEqual(result["status"], "INSUFFICIENT_DATA")

    def test_suspect_historical_readings_are_excluded(self):
        history = make_history()

        for reading in history:
            reading.data_quality = "SUSPECT"

        result = calculate_predictive_analytics(
            self.current,
            history,
        )

        self.assertEqual(result["status"], "INSUFFICIENT_DATA")
        self.assertEqual(result["historical_readings"], 0)

    def test_non_synthetic_historical_readings_are_excluded(self):
        history = make_history()

        for reading in history:
            reading.is_synthetic = False

        result = calculate_predictive_analytics(
            self.current,
            history,
        )

        self.assertEqual(result["status"], "INSUFFICIENT_DATA")

    def test_future_historical_readings_are_excluded(self):
        history = make_history()

        for reading in history:
            reading.recorded_at = self.current.recorded_at + timedelta(
                minutes=1
            )

        result = calculate_predictive_analytics(
            self.current,
            history,
        )

        self.assertEqual(result["status"], "INSUFFICIENT_DATA")

    def test_short_history_span_is_rejected(self):
        now = timezone.now()

        history = []

        for index in range(12):
            history.append(
                SimpleNamespace(
                    astronaut_id=35,
                    recorded_at=now - timedelta(seconds=30 - index),
                    data_quality="VALID",
                    is_synthetic=True,
                    heart_rate_bpm=75 + (index % 3),
                    spo2_percent=98 + (index % 3),
                    body_temperature_c=36.7 + ((index % 3) * 0.1),
                    respiratory_rate_bpm=15 + (index % 3),
                    id=index + 1,
                )
            )

        result = calculate_predictive_analytics(
            self.current,
            history,
        )

        self.assertEqual(result["status"], "INSUFFICIENT_DATA")

    def test_invalid_current_feature_is_rejected(self):
        current = make_reading(heart_rate=float("nan"))

        result = calculate_predictive_analytics(
            current,
            self.history,
        )

        self.assertEqual(result["status"], "INVALID_FEATURES")

    def test_invalid_historical_feature_is_rejected(self):
        history = make_history()
        history[0].heart_rate_bpm = float("inf")

        result = calculate_predictive_analytics(
            self.current,
            history,
        )

        self.assertEqual(result["status"], "INVALID_FEATURES")

    def test_timezone_naive_timestamp_is_rejected(self):
        current = make_reading()
        current.recorded_at = timezone.now().replace(tzinfo=None)

        result = calculate_predictive_analytics(
            current,
            self.history,
        )

        self.assertEqual(result["status"], "INVALID_READING")
