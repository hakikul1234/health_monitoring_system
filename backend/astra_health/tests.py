from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from datetime import timedelta

from django.utils import timezone

from rest_framework.test import APIClient

from astra_accounts.models import UserProfile
from astra_crew.models import Astronaut
from astra_missions.models import Mission
from .models import VitalSignReading


User = get_user_model()


class HealthReadingAPITests(TestCase):

    def setUp(self):

        self.client = APIClient()

        # Mission Control
        self.mc_user = User.objects.create_user(
            username="health_mc",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.mc_user,
            full_name="Health Mission Control",
            role=UserProfile.Role.MISSION_CONTROL
        )

        # First astronaut
        self.astronaut_user = User.objects.create_user(
            username="health_astronaut_1",
            password="TestPassword123!"
        )

        self.astronaut_profile = UserProfile.objects.create(
            user=self.astronaut_user,
            full_name="Health Astronaut One",
            role=UserProfile.Role.ASTRONAUT
        )

        self.astronaut = Astronaut.objects.create(
            profile=self.astronaut_profile,
            astronaut_code="HEALTH-TEST-001",
            call_sign="HEALTH-ONE"
        )

        # Second astronaut
        self.other_user = User.objects.create_user(
            username="health_astronaut_2",
            password="TestPassword123!"
        )

        self.other_profile = UserProfile.objects.create(
            user=self.other_user,
            full_name="Health Astronaut Two",
            role=UserProfile.Role.ASTRONAUT
        )

        self.other_astronaut = Astronaut.objects.create(
            profile=self.other_profile,
            astronaut_code="HEALTH-TEST-002",
            call_sign="HEALTH-TWO"
        )

        # Medical Officer
        self.medical_user = User.objects.create_user(
            username="health_medical",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.medical_user,
            full_name="Health Medical Officer",
            role=UserProfile.Role.MEDICAL_OFFICER
        )

        # Mission assigned to first astronaut
        self.mission = Mission.objects.create(
            mission_code="HEALTH-MISSION-001",
            mission_name="Health Test Mission",
            mission_type=Mission.MissionType.ORBITAL,
            status=Mission.Status.PLANNED,
            created_by=self.mc_user
        )

        self.mission.crew.add(self.astronaut)

        # First astronaut reading
        self.reading = VitalSignReading.objects.create(
            astronaut=self.astronaut,
            mission=self.mission,
            heart_rate_bpm=75,
            spo2_percent=98,
            body_temperature_c="36.70",
            respiratory_rate_bpm=16,
            recorded_at=timezone.now(),
            data_quality=VitalSignReading.DataQuality.VALID,
            data_source=VitalSignReading.DataSource.TEST_FIXTURE
        )

        # Second astronaut reading
        self.other_reading = VitalSignReading.objects.create(
            astronaut=self.other_astronaut,
            heart_rate_bpm=80,
            spo2_percent=97,
            body_temperature_c="36.80",
            respiratory_rate_bpm=17,
            recorded_at=timezone.now(),
            data_quality=VitalSignReading.DataQuality.VALID,
            data_source=VitalSignReading.DataSource.TEST_FIXTURE
        )

        self.list_url = reverse("health-reading-list-create")

    def test_mission_control_can_list_all_readings(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_astronaut_can_only_see_own_readings(self):

        self.client.force_authenticate(user=self.astronaut_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        self.assertEqual(
            response.data[0]["id"],
            self.reading.id
        )

    def test_astronaut_can_view_own_reading_detail(self):

        self.client.force_authenticate(user=self.astronaut_user)

        url = reverse(
            "health-reading-detail",
            args=[self.reading.id]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["id"],
            self.reading.id
        )

    def test_astronaut_cannot_view_other_reading_detail(self):

        self.client.force_authenticate(user=self.astronaut_user)

        url = reverse(
            "health-reading-detail",
            args=[self.other_reading.id]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_astronaut_can_analyze_own_reading(self):

        self.client.force_authenticate(user=self.astronaut_user)

        url = reverse(
            "health-reading-analysis",
            args=[self.reading.id]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["reading"]["id"],
            self.reading.id
        )

    def test_astronaut_cannot_analyze_other_reading(self):

        self.client.force_authenticate(user=self.astronaut_user)

        url = reverse(
            "health-reading-analysis",
            args=[self.other_reading.id]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_medical_officer_can_read_health_data(self):

        self.client.force_authenticate(user=self.medical_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_mission_control_can_create_health_reading(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.post(
            self.list_url,
            {
                "astronaut_id": self.astronaut.id,
                "mission_id": self.mission.id,
                "heart_rate_bpm": 78,
                "spo2_percent": 99,
                "body_temperature_c": "36.80",
                "respiratory_rate_bpm": 15,
                "recorded_at": timezone.now().isoformat(),
                "data_quality": "VALID",
                "data_source": "TEST_FIXTURE"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)

        self.assertTrue(
            VitalSignReading.objects.filter(
                astronaut=self.astronaut,
                heart_rate_bpm=78
            ).exists()
        )

    def test_astronaut_cannot_create_health_reading(self):

        self.client.force_authenticate(user=self.astronaut_user)

        response = self.client.post(
            self.list_url,
            {
                "astronaut_id": self.astronaut.id,
                "heart_rate_bpm": 75,
                "spo2_percent": 98,
                "body_temperature_c": "36.70",
                "respiratory_rate_bpm": 16,
                "recorded_at": timezone.now().isoformat()
            },
            format="json"
        )

        self.assertEqual(response.status_code, 403)

    def test_invalid_heart_rate_is_rejected(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.post(
            self.list_url,
            {
                "astronaut_id": self.astronaut.id,
                "heart_rate_bpm": 301,
                "spo2_percent": 98,
                "body_temperature_c": "36.70",
                "respiratory_rate_bpm": 16,
                "recorded_at": timezone.now().isoformat()
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("heart_rate_bpm", response.data)

    def test_invalid_spo2_is_rejected(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.post(
            self.list_url,
            {
                "astronaut_id": self.astronaut.id,
                "heart_rate_bpm": 75,
                "spo2_percent": 101,
                "body_temperature_c": "36.70",
                "respiratory_rate_bpm": 16,
                "recorded_at": timezone.now().isoformat()
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("spo2_percent", response.data)

    def test_unassigned_astronaut_mission_combination_is_rejected(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.post(
            self.list_url,
            {
                "astronaut_id": self.other_astronaut.id,
                "mission_id": self.mission.id,
                "heart_rate_bpm": 75,
                "spo2_percent": 98,
                "body_temperature_c": "36.70",
                "respiratory_rate_bpm": 16,
                "recorded_at": timezone.now().isoformat()
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("mission_id", response.data)

    def test_ungradable_reading_analysis_is_available(self):

        self.client.force_authenticate(user=self.mc_user)

        ungradable_reading = VitalSignReading.objects.create(
            astronaut=self.astronaut,
            mission=self.mission,
            heart_rate_bpm=0,
            spo2_percent=0,
            body_temperature_c="0.00",
            respiratory_rate_bpm=0,
            recorded_at=timezone.now(),
            data_quality=VitalSignReading.DataQuality.UNGRADABLE,
            data_source=VitalSignReading.DataSource.TEST_FIXTURE,
            quality_notes="Synthetic ungradable test fixture."
        )

        url = reverse(
            "health-reading-analysis",
            args=[ungradable_reading.id]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

        self.assertEqual(
            response.data["reading"]["data_quality"],
            "UNGRADABLE"
        )

        # Rule-based analysis must not interpret ungradable measurements.
        rule_result = response.data["analysis"]

        self.assertEqual(
            rule_result["status"],
            "INSUFFICIENT_DATA"
        )
        self.assertEqual(rule_result["severity"], "UNKNOWN")
        self.assertFalse(rule_result["is_anomalous"])
        self.assertEqual(rule_result["findings"], [])

        # Verify all independent engines return structured results.
        engine_results = {
            "ml_analysis": response.data["ml_analysis"],
            "personal_baseline": response.data["personal_baseline"],
            "predictive_analytics": response.data["predictive_analytics"],
        }

        for engine_name, engine_result in engine_results.items():
            with self.subTest(engine=engine_name):
                self.assertIsInstance(engine_result, dict)
                self.assertFalse(engine_result["clinical_validation"])
                self.assertEqual(
                    engine_result["status"],
                    "INSUFFICIENT_DATA"
                )

    def test_predictive_analysis_response_contains_all_engines(self):

        self.client.force_authenticate(user=self.mc_user)

        url = reverse(
            "health-reading-analysis",
            args=[self.reading.id]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        self.assertIn("analysis", response.data)
        self.assertIn("ml_analysis", response.data)
        self.assertIn("personal_baseline", response.data)
        self.assertIn("predictive_analytics", response.data)

        # Every engine must return a structured dictionary.
        for engine_name in (
            "analysis",
            "ml_analysis",
            "personal_baseline",
            "predictive_analytics",
        ):
            with self.subTest(engine=engine_name):
                self.assertIsInstance(
                    response.data[engine_name],
                    dict
                )

        self.assertIn("model_type", response.data["analysis"])
        self.assertIn("model_type", response.data["ml_analysis"])

        # These engines are research demonstrations, not clinically validated.
        for engine_name in (
            "ml_analysis",
            "personal_baseline",
            "predictive_analytics",
        ):
            with self.subTest(engine=engine_name):
                self.assertFalse(
                    response.data[engine_name]["clinical_validation"]
                )

        self.assertEqual(
            response.data["predictive_analytics"]["status"],
            "INSUFFICIENT_DATA"
        )

        self.assertEqual(
            response.data["predictive_analytics"]["historical_readings"],
            0
        )

        self.assertFalse(
            response.data["predictive_analytics"]["clinical_validation"]
        )

    def test_predictive_analysis_api_estimates_synthetic_trend(self):

        self.client.force_authenticate(user=self.mc_user)

        now = timezone.now()

        for index in range(12):

            VitalSignReading.objects.create(
                astronaut=self.astronaut,
                mission=self.mission,
                heart_rate_bpm=70 + index,
                spo2_percent=99 - (index % 3),
                body_temperature_c=f"{36.50 + (index * 0.01):.2f}",
                respiratory_rate_bpm=14 + (index % 4),
                recorded_at=now - timedelta(minutes=(12 - index) * 10),
                data_quality=VitalSignReading.DataQuality.VALID,
                data_source=VitalSignReading.DataSource.TEST_FIXTURE,
                is_synthetic=True,
            )

        self.reading.recorded_at = now
        self.reading.is_synthetic = True
        self.reading.save(
            update_fields=["recorded_at", "is_synthetic"]
        )

        url = reverse(
            "health-reading-analysis",
            args=[self.reading.id]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        predictive = response.data["predictive_analytics"]

        self.assertEqual(
            predictive["status"],
            "TREND_ESTIMATED"
        )

        self.assertEqual(
            predictive["historical_readings"],
            12
        )

        self.assertEqual(
            predictive["forecast_horizon_seconds"],
            300
        )

        self.assertFalse(predictive["clinical_validation"])

        self.assertEqual(
            set(predictive["features"].keys()),
            {
                "heart_rate_bpm",
                "spo2_percent",
                "body_temperature_c",
                "respiratory_rate_bpm",
            }
        )

    def test_predictive_analysis_rejects_ungradable_synthetic_reading(self):

        self.client.force_authenticate(user=self.mc_user)

        ungradable_reading = VitalSignReading.objects.create(
            astronaut=self.astronaut,
            mission=self.mission,
            heart_rate_bpm=0,
            spo2_percent=0,
            body_temperature_c="0.00",
            respiratory_rate_bpm=0,
            recorded_at=timezone.now(),
            data_quality=VitalSignReading.DataQuality.UNGRADABLE,
            data_source=VitalSignReading.DataSource.TEST_FIXTURE,
            is_synthetic=True,
            quality_notes="Synthetic ungradable predictive API fixture."
        )

        url = reverse(
            "health-reading-analysis",
            args=[ungradable_reading.id]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        predictive = response.data["predictive_analytics"]

        self.assertEqual(
            predictive["status"],
            "INSUFFICIENT_DATA"
        )

        self.assertEqual(
            predictive["historical_readings"],
            0
        )

        self.assertFalse(predictive["clinical_validation"])
