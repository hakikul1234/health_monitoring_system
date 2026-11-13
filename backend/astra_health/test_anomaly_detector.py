from types import SimpleNamespace

from django.test import SimpleTestCase

from astra_health.ai.anomaly_detector import (
    detect_reading_anomalies,
)


class RuleBasedAnomalyDetectorTests(SimpleTestCase):

    @staticmethod
    def make_reading(**overrides):

        values = {
            "heart_rate_bpm": 75,
            "spo2_percent": 98,
            "body_temperature_c": 36.7,
            "respiratory_rate_bpm": 15,
            "data_quality": "VALID",
            "is_synthetic": True,
        }

        values.update(overrides)

        return SimpleNamespace(**values)

    def test_normal_reading_has_no_findings(self):

        result = detect_reading_anomalies(
            self.make_reading()
        )

        self.assertEqual(result["status"], "NORMAL")
        self.assertEqual(result["severity"], "NORMAL")
        self.assertFalse(result["is_anomalous"])
        self.assertEqual(result["findings"], [])

    def test_high_heart_rate_generates_warning(self):

        result = detect_reading_anomalies(
            self.make_reading(
                heart_rate_bpm=120
            )
        )

        self.assertEqual(result["status"], "WARNING")
        self.assertTrue(result["is_anomalous"])

        self.assertIn(
            "HEART_RATE_OUTSIDE_DEMO_RANGE",
            [item["rule"] for item in result["findings"]],
        )

    def test_low_spo2_generates_critical_finding(self):

        result = detect_reading_anomalies(
            self.make_reading(
                spo2_percent=85
            )
        )

        self.assertEqual(result["status"], "CRITICAL")

        self.assertIn(
            "SPO2_CRITICAL_LOW",
            [item["rule"] for item in result["findings"]],
        )

    def test_multiple_findings_are_preserved(self):

        result = detect_reading_anomalies(
            self.make_reading(
                heart_rate_bpm=170,
                spo2_percent=82,
                body_temperature_c=39.2,
                respiratory_rate_bpm=35,
            )
        )

        self.assertEqual(result["status"], "CRITICAL")
        self.assertEqual(len(result["findings"]), 4)

        self.assertEqual(
            {item["severity"] for item in result["findings"]},
            {"CRITICAL"},
        )

    def test_critical_finding_takes_overall_precedence(self):

        result = detect_reading_anomalies(
            self.make_reading(
                heart_rate_bpm=120,
                spo2_percent=85,
            )
        )

        self.assertEqual(result["status"], "CRITICAL")

        severities = {
            item["severity"]
            for item in result["findings"]
        }

        self.assertIn("WARNING", severities)
        self.assertIn("CRITICAL", severities)

    def test_ungradable_reading_is_not_interpreted(self):

        result = detect_reading_anomalies(
            self.make_reading(
                data_quality="UNGRADABLE",
                heart_rate_bpm=170,
                spo2_percent=82,
                body_temperature_c=39.2,
                respiratory_rate_bpm=35,
            )
        )

        self.assertEqual(
            result["status"],
            "INSUFFICIENT_DATA",
        )

        self.assertEqual(result["severity"], "UNKNOWN")
        self.assertFalse(result["is_anomalous"])
        self.assertEqual(result["findings"], [])

    def test_suspect_reading_retains_quality_information(self):

        result = detect_reading_anomalies(
            self.make_reading(
                data_quality="SUSPECT",
                heart_rate_bpm=120,
            )
        )

        self.assertEqual(result["data_quality"], "SUSPECT")
        self.assertEqual(result["status"], "WARNING")
