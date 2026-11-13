from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient

from astra_accounts.models import UserProfile
from astra_crew.models import Astronaut
from astra_health.models import VitalSignReading
from astra_missions.models import Mission


User = get_user_model()


class SimulatorAPITests(TestCase):

    def setUp(self):

        self.client = APIClient()

        self.mc_user = User.objects.create_user(
            username="simulator_mc",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.mc_user,
            full_name="Simulator Mission Control",
            role=UserProfile.Role.MISSION_CONTROL
        )

        self.astronaut_user = User.objects.create_user(
            username="simulator_astronaut",
            password="TestPassword123!"
        )

        self.astronaut_profile = UserProfile.objects.create(
            user=self.astronaut_user,
            full_name="Simulator Test Astronaut",
            role=UserProfile.Role.ASTRONAUT
        )

        self.astronaut = Astronaut.objects.create(
            profile=self.astronaut_profile,
            astronaut_code="SIM-TEST-001",
            call_sign="SIM-ONE"
        )

        self.medical_user = User.objects.create_user(
            username="simulator_medical",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.medical_user,
            full_name="Simulator Medical Officer",
            role=UserProfile.Role.MEDICAL_OFFICER
        )

        self.mission = Mission.objects.create(
            mission_code="SIM-TEST-MISSION",
            mission_name="Simulator Test Mission",
            mission_type=Mission.MissionType.ORBITAL,
            status=Mission.Status.PLANNED,
            created_by=self.mc_user
        )

        self.mission.crew.add(self.astronaut)

        self.url = reverse("telemetry-generate")

    def generate(self, scenario, **extra):

        payload = {
            "astronaut_id": self.astronaut.id,
            "mission_id": self.mission.id,
            "scenario": scenario,
            "count": 3,
            "interval_seconds": 60,
            "seed": 20261112,
        }

        payload.update(extra)

        return self.client.post(
            self.url,
            payload,
            format="json"
        )

    def test_normal_scenario_generates_valid_synthetic_readings(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate("NORMAL_MISSION")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["readings"]), 3)

        self.assertEqual(
            response.data["scenario"],
            "NORMAL_MISSION"
        )

        for reading in response.data["readings"]:

            self.assertEqual(reading["data_quality"], "VALID")
            self.assertTrue(reading["is_synthetic"])
            self.assertEqual(reading["data_source"], "SIMULATOR")

        self.assertTrue(
            response.data["summary"]["all_synthetic"]
        )

    def test_health_anomaly_scenario_generates_suspect_readings(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate("HEALTH_ANOMALY")

        self.assertEqual(response.status_code, 201)

        for reading in response.data["readings"]:

            self.assertEqual(reading["data_quality"], "SUSPECT")
            self.assertGreaterEqual(reading["heart_rate_bpm"], 110)
            self.assertLessEqual(reading["heart_rate_bpm"], 145)

            self.assertGreaterEqual(reading["spo2_percent"], 88)
            self.assertLessEqual(reading["spo2_percent"], 94)

        self.assertGreater(
            response.data["alert_generation"]["created_alerts"],
            0
        )

    def test_emergency_scenario_generates_expected_values(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate("EMERGENCY_MISSION")

        self.assertEqual(response.status_code, 201)

        for reading in response.data["readings"]:

            self.assertEqual(reading["data_quality"], "SUSPECT")

            self.assertGreaterEqual(
                reading["heart_rate_bpm"], 150
            )

            self.assertLessEqual(
                reading["heart_rate_bpm"], 180
            )

            self.assertGreaterEqual(
                reading["spo2_percent"], 80
            )

            self.assertLessEqual(
                reading["spo2_percent"], 87
            )

    def test_data_quality_fault_is_not_interpreted_as_valid_data(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate("DATA_QUALITY_FAULT")

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            response.data["alert_generation"][
                "insufficient_data_readings"
            ],
            3
        )

        self.assertEqual(
            response.data["alert_generation"]["created_alerts"],
            0
        )

        for reading in response.data["readings"]:

            self.assertEqual(
                reading["data_quality"],
                "UNGRADABLE"
            )

        self.assertEqual(
            VitalSignReading.objects.filter(
                astronaut=self.astronaut,
                data_quality="UNGRADABLE"
            ).count(),
            3
        )

    def test_astronaut_cannot_generate_telemetry(self):

        self.client.force_authenticate(
            user=self.astronaut_user
        )

        response = self.generate("NORMAL_MISSION")

        self.assertEqual(response.status_code, 403)

        self.assertEqual(
            VitalSignReading.objects.count(),
            0
        )

    def test_medical_officer_cannot_generate_telemetry(self):

        self.client.force_authenticate(
            user=self.medical_user
        )

        response = self.generate("NORMAL_MISSION")

        self.assertEqual(response.status_code, 403)

        self.assertEqual(
            VitalSignReading.objects.count(),
            0
        )

    def test_unsupported_scenario_is_rejected(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate("INVALID_SCENARIO")

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            VitalSignReading.objects.count(),
            0
        )

    def test_batch_count_above_limit_is_rejected(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.generate(
            "NORMAL_MISSION",
            count=1001
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            VitalSignReading.objects.count(),
            0
        )

    def test_unassigned_astronaut_mission_is_rejected(self):

        self.client.force_authenticate(user=self.mc_user)

        other_user = User.objects.create_user(
            username="simulator_other",
            password="TestPassword123!"
        )

        other_profile = UserProfile.objects.create(
            user=other_user,
            full_name="Unassigned Astronaut",
            role=UserProfile.Role.ASTRONAUT
        )

        other_astronaut = Astronaut.objects.create(
            profile=other_profile,
            astronaut_code="SIM-TEST-002",
            call_sign="SIM-TWO"
        )

        response = self.client.post(
            self.url,
            {
                "astronaut_id": other_astronaut.id,
                "mission_id": self.mission.id,
                "scenario": "NORMAL_MISSION",
                "count": 3,
                "seed": 100
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            VitalSignReading.objects.count(),
            0
        )

    def test_generated_readings_follow_requested_interval(self):

        self.client.force_authenticate(user=self.mc_user)

        start_at = timezone.now() - timedelta(minutes=5)

        response = self.generate(
            "NORMAL_MISSION",
            start_at=start_at.isoformat(),
            count=3,
            interval_seconds=120
        )

        self.assertEqual(response.status_code, 201)

        readings = response.data["readings"]

        first_time = timezone.datetime.fromisoformat(
            readings[0]["recorded_at"]
        )

        second_time = timezone.datetime.fromisoformat(
            readings[1]["recorded_at"]
        )

        third_time = timezone.datetime.fromisoformat(
            readings[2]["recorded_at"]
        )

        self.assertEqual(
            (second_time - first_time).total_seconds(),
            120
        )

        self.assertEqual(
            (third_time - second_time).total_seconds(),
            120
        )

    def test_same_seed_produces_reproducible_values(self):

        self.client.force_authenticate(user=self.mc_user)

        first_response = self.generate(
            "NORMAL_MISSION",
            count=3,
            seed=98765
        )

        second_response = self.generate(
            "NORMAL_MISSION",
            count=3,
            seed=98765
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)

        fields = [
            "heart_rate_bpm",
            "spo2_percent",
            "body_temperature_c",
            "respiratory_rate_bpm",
            "data_quality",
        ]

        for index in range(3):

            for field in fields:

                self.assertEqual(
                    first_response.data["readings"][index][field],
                    second_response.data["readings"][index][field]
                )
