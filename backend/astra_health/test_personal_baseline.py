from datetime import timedelta
from types import SimpleNamespace

from django.test import SimpleTestCase
from django.utils import timezone

from astra_health.ai.personal_baseline import (
    calculate_personal_baseline,
    MIN_BASELINE_READINGS,
)


class PersonalBaselineTests(SimpleTestCase):

    def setUp(self):
        self.now = timezone.now()

    @staticmethod
    def make_reading(
        astronaut_id=1,
        recorded_at=None,
        **overrides
    ):
        values = {
            "astronaut_id": astronaut_id,
            "recorded_at": recorded_at or timezone.now(),
            "is_synthetic": True,
            "data_quality": "VALID",
            "heart_rate_bpm": 75,
            "spo2_percent": 98,
            "body_temperature_c": 36.7,
            "respiratory_rate_bpm": 15,
        }

        values.update(overrides)

        return SimpleNamespace(**values)

    def make_history(self, count=12, **overrides):
        history = []

        for i in range(count):
            variation = (i % 3) - 1

            values = {
                "heart_rate_bpm": 75 + variation,
                "spo2_percent": 98 + variation,
                "body_temperature_c": 36.7 + (variation * 0.1),
                "respiratory_rate_bpm": 15 + variation,
            }

            values.update(overrides)

            history.append(
                self.make_reading(
                    recorded_at=self.now - timedelta(minutes=10 * i + 1),
                    **values
                )
            )

        return history

    def test_insufficient_history_is_rejected(self):
        current = self.make_reading(recorded_at=self.now)

        result = calculate_personal_baseline(
            current,
            self.make_history(9),
        )

        self.assertEqual(
            result["status"],
            "INSUFFICIENT_DATA",
        )

        self.assertEqual(
            result["baseline_readings"],
            9,
        )

    def test_normal_reading_is_within_baseline(self):
        current = self.make_reading(
            recorded_at=self.now,
        )

        result = calculate_personal_baseline(
            current,
            self.make_history(12),
        )

        self.assertEqual(
            result["status"],
            "WITHIN_BASELINE",
        )

        self.assertEqual(
            result["baseline_readings"],
            12,
        )

    def test_large_deviation_is_detected(self):
        current = self.make_reading(
            recorded_at=self.now,
            heart_rate_bpm=150,
        )

        result = calculate_personal_baseline(
            current,
            self.make_history(12),
        )

        self.assertEqual(
            result["status"],
            "DEVIATION",
        )

        self.assertTrue(
            result["features"]["heart_rate_bpm"]["deviation_detected"]
        )

    def test_other_astronaut_history_is_excluded(self):
        current = self.make_reading(
            astronaut_id=1,
            recorded_at=self.now,
        )

        history = self.make_history(
            12,
            astronaut_id=2,
        )

        result = calculate_personal_baseline(
            current,
            history,
        )

        self.assertEqual(
            result["status"],
            "INSUFFICIENT_DATA",
        )

    def test_ungradable_current_reading_is_blocked(self):
        current = self.make_reading(
            recorded_at=self.now,
            data_quality="UNGRADABLE",
            heart_rate_bpm=180,
        )

        result = calculate_personal_baseline(
            current,
            self.make_history(12),
        )

        self.assertEqual(
            result["status"],
            "INSUFFICIENT_DATA",
        )

        self.assertEqual(
            result["baseline_readings"],
            0,
        )

    def test_suspect_history_is_excluded(self):
        current = self.make_reading(
            recorded_at=self.now,
        )

        history = self.make_history(12)

        history[0].data_quality = "SUSPECT"

        result = calculate_personal_baseline(
            current,
            history,
        )

        self.assertEqual(
            result["baseline_readings"],
            11,
        )

    def test_non_synthetic_current_reading_is_not_evaluated(self):
        current = self.make_reading(
            recorded_at=self.now,
            is_synthetic=False,
        )

        result = calculate_personal_baseline(
            current,
            self.make_history(12),
        )

        self.assertEqual(
            result["status"],
            "NOT_EVALUATED",
        )

    def test_current_and_future_readings_are_excluded(self):
        current = self.make_reading(
            recorded_at=self.now,
        )

        history = self.make_history(12)

        history.append(
            self.make_reading(
                recorded_at=self.now,
            )
        )

        history.append(
            self.make_reading(
                recorded_at=self.now + timedelta(minutes=5),
            )
        )

        result = calculate_personal_baseline(
            current,
            history,
        )

        self.assertEqual(
            result["baseline_readings"],
            12,
        )

    def test_old_readings_are_excluded(self):
        current = self.make_reading(
            recorded_at=self.now,
        )

        history = [
            self.make_reading(
                recorded_at=self.now - timedelta(days=31),
            )
            for _ in range(12)
        ]

        result = calculate_personal_baseline(
            current,
            history,
        )

        self.assertEqual(
            result["status"],
            "INSUFFICIENT_DATA",
        )

    def test_zero_mad_is_handled_without_division_error(self):
        current = self.make_reading(
            recorded_at=self.now,
            heart_rate_bpm=100,
        )

        history = self.make_history(12)

        for item in history:
            item.heart_rate_bpm = 75

        result = calculate_personal_baseline(
            current,
            history,
        )

        heart_rate = result["features"]["heart_rate_bpm"]

        self.assertEqual(
            heart_rate["status"],
            "ZERO_MAD",
        )

        self.assertIsNone(
            heart_rate["robust_z_score"],
        )

    def test_baseline_sample_limit_is_enforced(self):
        current = self.make_reading(
            recorded_at=self.now,
        )

        history = self.make_history(120)

        result = calculate_personal_baseline(
            current,
            history,
        )

        self.assertEqual(
            result["baseline_readings"],
            100,
        )
