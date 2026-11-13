from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from astra_missions.models import Mission
from astra_simulator.models import HabitatTelemetry
from astra_simulator.services.habitat_simulator import (
    generate_habitat_values,
    generate_habitat_telemetry_batch,
    get_habitat_telemetry_summary,
    get_available_habitat_scenarios,
)


User = get_user_model()


class HabitatSimulatorEngineTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="habitat_test_user",
            password="TestPassword123!"
        )

        self.mission = Mission.objects.create(
            mission_code="HAB-TEST-001",
            mission_name="Habitat Simulator Test",
            mission_type=Mission.MissionType.ORBITAL,
            status=Mission.Status.PLANNED,
            created_by=self.user,
        )

        self.start_at = timezone.now().replace(microsecond=0)

    def test_all_five_scenarios_are_registered(self):
        scenarios = get_available_habitat_scenarios()

        self.assertEqual(len(scenarios), 5)

        self.assertEqual(
            set(scenarios),
            {
                "NORMAL_HABITAT",
                "ELEVATED_CO2",
                "PRESSURE_DEVIATION",
                "TEMPERATURE_HUMIDITY_ANOMALY",
                "SENSOR_QUALITY_FAULT",
            }
        )

    def test_seed_produces_reproducible_values(self):
        first = generate_habitat_values(
            "NORMAL_HABITAT",
            seed=20261112
        )

        second = generate_habitat_values(
            "NORMAL_HABITAT",
            seed=20261112
        )

        self.assertEqual(first, second)

    def test_scenario_quality_and_value_ranges(self):
        normal = generate_habitat_values(
            "NORMAL_HABITAT",
            seed=101
        )

        elevated = generate_habitat_values(
            "ELEVATED_CO2",
            seed=102
        )

        pressure = generate_habitat_values(
            "PRESSURE_DEVIATION",
            seed=103
        )

        temperature = generate_habitat_values(
            "TEMPERATURE_HUMIDITY_ANOMALY",
            seed=104
        )

        fault = generate_habitat_values(
            "SENSOR_QUALITY_FAULT",
            seed=105
        )

        self.assertEqual(normal["data_quality"], "VALID")

        self.assertEqual(elevated["data_quality"], "SUSPECT")
        self.assertGreaterEqual(
            elevated["carbon_dioxide_ppm"], 5000
        )
        self.assertLessEqual(
            elevated["carbon_dioxide_ppm"], 15000
        )

        self.assertEqual(pressure["data_quality"], "SUSPECT")
        self.assertTrue(
            float(pressure["cabin_pressure_kpa"]) <= 60
            or float(pressure["cabin_pressure_kpa"]) >= 115
        )

        self.assertEqual(temperature["data_quality"], "SUSPECT")
        self.assertGreaterEqual(
            float(temperature["cabin_temperature_c"]), 30
        )
        self.assertGreaterEqual(
            float(temperature["relative_humidity_percent"]), 75
        )

        self.assertEqual(fault["data_quality"], "UNGRADABLE")
        self.assertIn("placeholders", fault["quality_notes"])

    def test_batch_persists_synthetic_records_chronologically(self):
        records = generate_habitat_telemetry_batch(
            mission=self.mission,
            scenario="NORMAL_HABITAT",
            count=4,
            interval_seconds=30,
            seed=20261112,
            start_at=self.start_at,
        )

        self.assertEqual(len(records), 4)
        self.assertEqual(
            HabitatTelemetry.objects.filter(
                mission=self.mission
            ).count(),
            4
        )

        for index, record in enumerate(records):
            self.assertTrue(record.is_synthetic)
            self.assertEqual(record.data_quality, "VALID")
            self.assertEqual(record.mission_id, self.mission.id)

            self.assertEqual(
                record.recorded_at,
                self.start_at + timedelta(seconds=index * 30)
            )

    def test_invalid_batch_parameters_are_rejected(self):
        with self.assertRaises(ValueError):
            generate_habitat_telemetry_batch(
                mission=self.mission,
                count=0
            )

        with self.assertRaises(ValueError):
            generate_habitat_telemetry_batch(
                mission=self.mission,
                count=1001
            )

        with self.assertRaises(ValueError):
            generate_habitat_telemetry_batch(
                mission=self.mission,
                interval_seconds=0
            )

        with self.assertRaises(ValueError):
            generate_habitat_telemetry_batch(
                mission=self.mission,
                scenario="UNKNOWN_SCENARIO"
            )

    def test_naive_timestamp_is_rejected(self):
        from datetime import datetime

        with self.assertRaises(ValueError):
            generate_habitat_telemetry_batch(
                mission=self.mission,
                start_at=datetime(2026, 11, 12, 12, 0, 0)
            )

    def test_ungradable_records_are_excluded_from_averages(self):
        valid = generate_habitat_telemetry_batch(
            mission=self.mission,
            scenario="NORMAL_HABITAT",
            count=1,
            seed=301,
            start_at=self.start_at,
        )

        ungradable = generate_habitat_telemetry_batch(
            mission=self.mission,
            scenario="SENSOR_QUALITY_FAULT",
            count=1,
            seed=302,
            start_at=self.start_at + timedelta(minutes=1),
        )

        summary = get_habitat_telemetry_summary(
            list(valid) + list(ungradable)
        )

        self.assertEqual(summary["total_readings"], 2)
        self.assertEqual(
            summary["data_quality_counts"]["UNGRADABLE"], 1
        )

        self.assertEqual(
            summary["average_carbon_dioxide_ppm"],
            valid[0].carbon_dioxide_ppm
        )

    def test_all_ungradable_records_produce_no_environmental_averages(self):
        records = generate_habitat_telemetry_batch(
            mission=self.mission,
            scenario="SENSOR_QUALITY_FAULT",
            count=3,
            seed=303,
            start_at=self.start_at,
        )

        summary = get_habitat_telemetry_summary(records)

        self.assertEqual(summary["total_readings"], 3)
        self.assertEqual(
            summary["data_quality_counts"]["UNGRADABLE"], 3
        )

        average_fields = [
            "average_oxygen_partial_pressure_kpa",
            "average_carbon_dioxide_ppm",
            "average_cabin_pressure_kpa",
            "average_cabin_temperature_c",
            "average_relative_humidity_percent",
        ]

        for field in average_fields:
            with self.subTest(field=field):
                self.assertIsNone(summary[field])

    def test_empty_summary(self):
        summary = get_habitat_telemetry_summary([])

        self.assertEqual(summary["total_readings"], 0)
        self.assertIsNone(
            summary["average_carbon_dioxide_ppm"]
        )
        self.assertTrue(summary["all_synthetic"])
