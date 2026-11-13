from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient

from astra_accounts.models import UserProfile
from astra_missions.models import Mission
from astra_simulator.models import HabitatTelemetry


User = get_user_model()


class HabitatTelemetryAPITests(TestCase):

    def setUp(self):

        self.client = APIClient()

        self.mc_user = User.objects.create_user(
            username="habitat_api_mc",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.mc_user,
            full_name="Habitat Mission Control",
            role=UserProfile.Role.MISSION_CONTROL
        )

        self.admin_user = User.objects.create_user(
            username="habitat_api_admin",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.admin_user,
            full_name="Habitat System Admin",
            role=UserProfile.Role.SYSTEM_ADMIN
        )

        self.astronaut_user = User.objects.create_user(
            username="habitat_api_astronaut",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.astronaut_user,
            full_name="Habitat Test Astronaut",
            role=UserProfile.Role.ASTRONAUT
        )

        self.medical_user = User.objects.create_user(
            username="habitat_api_medical",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.medical_user,
            full_name="Habitat Medical Officer",
            role=UserProfile.Role.MEDICAL_OFFICER
        )

        self.mission = Mission.objects.create(
            mission_code="HAB-API-001",
            mission_name="Habitat API Test Mission",
            mission_type=Mission.MissionType.ORBITAL,
            status=Mission.Status.PLANNED,
            created_by=self.mc_user
        )

        self.url = reverse("habitat-telemetry-generate")

    def generate(self, scenario="NORMAL_HABITAT", **extra):

        payload = {
            "mission_id": self.mission.id,
            "scenario": scenario,
            "count": 3,
            "interval_seconds": 60,
            "seed": 20261113,
        }

        payload.update(extra)

        return self.client.post(
            self.url,
            payload,
            format="json"
        )

    def test_mission_control_can_generate_habitat_telemetry(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate()

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["readings"]), 3)

        self.assertEqual(
            response.data["mission"]["id"],
            self.mission.id
        )

        self.assertEqual(
            response.data["scenario"],
            "NORMAL_HABITAT"
        )

        self.assertTrue(
            response.data["summary"]["all_synthetic"]
        )

        self.assertEqual(
            HabitatTelemetry.objects.filter(
                mission=self.mission
            ).count(),
            3
        )

    def test_system_admin_can_generate_habitat_telemetry(self):

        self.client.force_authenticate(user=self.admin_user)

        response = self.generate()

        self.assertEqual(response.status_code, 201)

    def test_unauthenticated_user_is_rejected(self):

        response = self.generate()

        self.assertEqual(response.status_code, 401)

        self.assertEqual(
            HabitatTelemetry.objects.count(),
            0
        )

    def test_astronaut_cannot_generate_habitat_telemetry(self):

        self.client.force_authenticate(user=self.astronaut_user)

        response = self.generate()

        self.assertEqual(response.status_code, 403)

        self.assertEqual(
            HabitatTelemetry.objects.count(),
            0
        )

    def test_medical_officer_cannot_generate_habitat_telemetry(self):

        self.client.force_authenticate(user=self.medical_user)

        response = self.generate()

        self.assertEqual(response.status_code, 403)

        self.assertEqual(
            HabitatTelemetry.objects.count(),
            0
        )

    def test_missing_mission_is_rejected(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate(
            mission_id=999999
        )

        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            HabitatTelemetry.objects.count(),
            0
        )

    def test_invalid_scenario_is_rejected(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate(
            scenario="INVALID_HABITAT"
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            HabitatTelemetry.objects.count(),
            0
        )

    def test_batch_above_limit_is_rejected(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate(
            count=1001
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            HabitatTelemetry.objects.count(),
            0
        )

    def test_all_five_scenarios_generate_expected_quality(self):

        self.client.force_authenticate(user=self.mc_user)

        scenarios = {
            "NORMAL_HABITAT": "VALID",
            "ELEVATED_CO2": "SUSPECT",
            "PRESSURE_DEVIATION": "SUSPECT",
            "TEMPERATURE_HUMIDITY_ANOMALY": "SUSPECT",
            "SENSOR_QUALITY_FAULT": "UNGRADABLE",
        }

        for scenario, expected_quality in scenarios.items():

            with self.subTest(scenario=scenario):

                response = self.generate(
                    scenario=scenario,
                    count=1
                )

                self.assertEqual(response.status_code, 201)

                self.assertEqual(
                    response.data["readings"][0]["data_quality"],
                    expected_quality
                )

    def test_ungradable_sensor_placeholders_are_not_averaged(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate(
            scenario="SENSOR_QUALITY_FAULT",
            count=2
        )

        self.assertEqual(response.status_code, 201)

        summary = response.data["summary"]

        self.assertEqual(summary["total_readings"], 2)

        self.assertEqual(
            summary["data_quality_counts"]["UNGRADABLE"],
            2
        )

        self.assertIsNone(
            summary["average_carbon_dioxide_ppm"]
        )

        self.assertIsNone(
            summary["average_cabin_pressure_kpa"]
        )

        self.assertIsNone(
            summary["average_oxygen_partial_pressure_kpa"]
        )

        for reading in response.data["readings"]:

            self.assertIn(
                "placeholders",
                reading["quality_notes"]
            )

    def test_response_contains_synthetic_data_disclaimer(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate()

        self.assertEqual(response.status_code, 201)

        disclaimer = response.data["disclaimer"]

        self.assertIn("SIMULATED DATA ONLY", disclaimer)
        self.assertIn("not real spacecraft telemetry", disclaimer)
        self.assertIn("safety thresholds", disclaimer)

    def test_requested_sensor_id_is_preserved(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate(
            sensor_id="SIM-HAB-CABIN-02"
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            response.data["sensor_id"],
            "SIM-HAB-CABIN-02"
        )

        self.assertEqual(
            response.data["readings"][0]["sensor_id"],
            "SIM-HAB-CABIN-02"
        )

    def test_requested_interval_is_preserved(self):

        self.client.force_authenticate(user=self.mc_user)

        start_at = timezone.now().replace(microsecond=0) - timedelta(
            minutes=5
        )

        response = self.generate(
            count=3,
            interval_seconds=120,
            start_at=start_at.isoformat()
        )

        self.assertEqual(response.status_code, 201)

        readings = response.data["readings"]

        first = timezone.datetime.fromisoformat(
            readings[0]["recorded_at"]
        )

        second = timezone.datetime.fromisoformat(
            readings[1]["recorded_at"]
        )

        third = timezone.datetime.fromisoformat(
            readings[2]["recorded_at"]
        )

        self.assertEqual(
            (second - first).total_seconds(),
            120
        )

        self.assertEqual(
            (third - second).total_seconds(),
            120
        )

    def test_invalid_sensor_id_is_rejected(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate(
            sensor_id=" " * 5
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            HabitatTelemetry.objects.count(),
            0
        )
