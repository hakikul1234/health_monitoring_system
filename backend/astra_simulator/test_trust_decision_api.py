from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient

from astra_accounts.models import UserProfile
from astra_crew.models import Astronaut
from astra_health.models import (
    SensorSimulationRun,
    VirtualHealthSensor,
    VitalSignReading,
)
from astra_missions.models import Mission


User = get_user_model()


class TrustDecisionAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.mc_user = User.objects.create_user(
            username="trust_api_mc",
            password="TestPassword123!",
        )
        UserProfile.objects.create(
            user=self.mc_user,
            full_name="Trust API Mission Control",
            role=UserProfile.Role.MISSION_CONTROL,
        )

        self.medical_user = User.objects.create_user(
            username="trust_api_medical",
            password="TestPassword123!",
        )
        UserProfile.objects.create(
            user=self.medical_user,
            full_name="Trust API Medical Officer",
            role=UserProfile.Role.MEDICAL_OFFICER,
        )

        astronaut_user = User.objects.create_user(
            username="trust_api_astronaut",
            password="TestPassword123!",
        )
        astronaut_profile = UserProfile.objects.create(
            user=astronaut_user,
            full_name="Trust API Astronaut",
            role=UserProfile.Role.ASTRONAUT,
        )

        self.astronaut = Astronaut.objects.create(
            profile=astronaut_profile,
            astronaut_code="TRUST-API-001",
            call_sign="TRUST-API",
        )

        self.mission = Mission.objects.create(
            mission_code="TRUST-API-MISSION",
            mission_name="Trust API Test Mission",
            mission_type=Mission.MissionType.ORBITAL,
            status=Mission.Status.PLANNED,
            created_by=self.mc_user,
        )
        self.mission.crew.add(self.astronaut)

        self.sensor = self.make_sensor("TRUST-API-SENSOR-001")
        self.run = self.make_run(self.sensor)
        self.reading = self.make_reading(self.sensor, self.run)

        self.url = reverse("trust-decision-evaluate")
        self.client.force_authenticate(user=self.mc_user)

        self.normal_analysis = {
            "status": "NORMAL",
            "is_anomalous": False,
            "findings": [],
            "model_type": "TEST_RULE_ENGINE",
        }

        self.anomalous_analysis = {
            "status": "WARNING",
            "is_anomalous": True,
            "findings": [{"rule": "TEST_ANOMALY"}],
            "model_type": "TEST_RULE_ENGINE",
        }

    def make_sensor(self, code):
        return VirtualHealthSensor.objects.create(
            sensor_code=code,
            astronaut=self.astronaut,
            mission=self.mission,
            manufacturer="ASTRA Test Systems",
            model_number="TRUST-API-TEST",
            firmware_version="1.0.0",
        )

    def make_run(self, sensor):
        return SensorSimulationRun.objects.create(
            sensor=sensor,
            fault_mode=SensorSimulationRun.FaultMode.NORMAL,
            status=SensorSimulationRun.RunStatus.COMPLETED,
            requested_count=1,
            generated_count=1,
            completed_at=timezone.now(),
        )

    def make_reading(self, sensor, run):
        return VitalSignReading.objects.create(
            astronaut=self.astronaut,
            mission=self.mission,
            sensor=sensor,
            simulation_run=run,
            heart_rate_bpm=75,
            spo2_percent=98,
            body_temperature_c="36.80",
            respiratory_rate_bpm=16,
            recorded_at=timezone.now(),
            data_quality=VitalSignReading.DataQuality.VALID,
            data_source=VitalSignReading.DataSource.SIMULATOR,
            is_synthetic=True,
        )

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_mission_control_can_evaluate_reading(self, detector):
        detector.return_value = self.normal_analysis

        response = self.client.post(
            self.url,
            {"reading_id": self.reading.id},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["trust_decision"]["decision"],
            "ACCEPT",
        )
        self.assertEqual(
            response.data["reading_id"],
            self.reading.id,
        )

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_independent_sensor_returns_cross_check(self, detector):
        second_sensor = self.make_sensor("TRUST-API-SENSOR-002")
        second_run = self.make_run(second_sensor)
        second_reading = self.make_reading(second_sensor, second_run)

        detector.side_effect = [
            self.anomalous_analysis,
            self.normal_analysis,
        ]

        response = self.client.post(
            self.url,
            {
                "reading_id": self.reading.id,
                "cross_check_reading_id": second_reading.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["trust_decision"]["decision"],
            "CROSS_CHECK",
        )
        self.assertFalse(
            response.data["trust_decision"]["evidence"]
            ["independent_reading"]["comparison_performed"]
        )
        self.assertEqual(
            response.data["cross_check_reading_id"],
            second_reading.id,
        )

    def test_medical_officer_is_forbidden(self):
        self.client.force_authenticate(user=self.medical_user)

        response = self.client.post(
            self.url,
            {"reading_id": self.reading.id},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_request_is_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.url,
            {"reading_id": self.reading.id},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

    def test_missing_reading_returns_404(self):
        response = self.client.post(
            self.url,
            {"reading_id": 999999},
            format="json",
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.data["success"])

    def test_same_reading_cannot_be_submitted_as_cross_check(self):
        response = self.client.post(
            self.url,
            {
                "reading_id": self.reading.id,
                "cross_check_reading_id": self.reading.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "cross_check_reading_id",
            response.data["errors"],
        )

    def test_missing_reading_id_returns_400(self):
        response = self.client.post(
            self.url,
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_missing_cross_check_reading_returns_404(self):
        response = self.client.post(
            self.url,
            {
                "reading_id": self.reading.id,
                "cross_check_reading_id": 999999,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 404)


