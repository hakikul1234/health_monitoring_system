from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from astra_accounts.models import UserProfile
from astra_crew.models import Astronaut
from astra_health.models import (
    VirtualHealthSensor,
    VitalSignReading,
)
from astra_missions.models import Mission


User = get_user_model()


class VirtualSensorAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.mc_user = User.objects.create_user(
            username="virtual_sensor_mc",
            password="TestPassword123!",
        )

        UserProfile.objects.create(
            user=self.mc_user,
            full_name="Virtual Sensor Mission Control",
            role=UserProfile.Role.MISSION_CONTROL,
        )

        self.astronaut_user = User.objects.create_user(
            username="virtual_sensor_astronaut",
            password="TestPassword123!",
        )

        self.astronaut_profile = UserProfile.objects.create(
            user=self.astronaut_user,
            full_name="Virtual Sensor Astronaut",
            role=UserProfile.Role.ASTRONAUT,
        )

        self.astronaut = Astronaut.objects.create(
            profile=self.astronaut_profile,
            astronaut_code="VS-TEST-001",
            call_sign="VS-ONE",
        )

        self.medical_user = User.objects.create_user(
            username="virtual_sensor_medical",
            password="TestPassword123!",
        )

        UserProfile.objects.create(
            user=self.medical_user,
            full_name="Virtual Sensor Medical Officer",
            role=UserProfile.Role.MEDICAL_OFFICER,
        )

        self.mission = Mission.objects.create(
            mission_code="VS-TEST-MISSION",
            mission_name="Virtual Sensor Test Mission",
            mission_type=Mission.MissionType.ORBITAL,
            status=Mission.Status.PLANNED,
            created_by=self.mc_user,
        )

        self.mission.crew.add(self.astronaut)

        self.registration_url = reverse(
            "virtual-health-sensor-list-create"
        )

        self.client.force_authenticate(user=self.mc_user)

        registration = self.client.post(
            self.registration_url,
            {
                "sensor_code": "VS-WEARABLE-001",
                "astronaut_id": self.astronaut.id,
                "mission_id": self.mission.id,
                "manufacturer": "ASTRA Synthetic Systems",
                "model_number": "VS-DEMO-01",
                "firmware_version": "1.0.0",
            },
            format="json",
        )

        if registration.status_code != 201:
            raise AssertionError(
                "Test sensor registration failed: "
                f"{registration.status_code} {registration.data}"
            )

        self.sensor = VirtualHealthSensor.objects.get(
            sensor_code="VS-WEARABLE-001"
        )

    def simulate(self, **extra):
        payload = {
            "scenario": "NORMAL_MISSION",
            "fault_mode": "NORMAL",
            "count": 3,
            "interval_seconds": 60,
            "seed": 20261113,
        }

        payload.update(extra)

        url = reverse(
            "virtual-health-sensor-simulate",
            kwargs={"sensor_id": self.sensor.id},
        )

        return self.client.post(
            url,
            payload,
            format="json",
        )

    def test_sensor_registration_creates_synthetic_sensor(self):
        self.assertTrue(self.sensor.is_synthetic)
        self.assertEqual(
            self.sensor.astronaut_id,
            self.astronaut.id,
        )
        self.assertEqual(
            self.sensor.mission_id,
            self.mission.id,
        )

    def test_normal_mode_generates_linked_readings(self):
        response = self.simulate()

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["readings"]), 3)

        for reading in response.data["readings"]:
            self.assertTrue(reading["is_synthetic"])
            self.assertEqual(
                reading["sensor_id"],
                self.sensor.id,
            )
            self.assertIsNotNone(
                reading["simulation_run_id"]
            )

        self.assertEqual(
            VitalSignReading.objects.filter(
                sensor=self.sensor
            ).count(),
            3,
        )

    def test_noise_mode_marks_readings_suspect_and_suppresses_health_alerts(self):
        response = self.simulate(
            scenario="HEALTH_ANOMALY",
            fault_mode="NOISE",
            noise_level_percent=5,
        )

        self.assertEqual(response.status_code, 201)

        for reading in response.data["readings"]:
            self.assertEqual(
                reading["data_quality"],
                "SUSPECT",
            )

        self.assertEqual(
            response.data["alert_generation"]["pipeline"],
            "SENSOR_FAULT_OBSERVATION_ONLY",
        )

    def test_dropout_mode_records_only_received_packets(self):
        response = self.simulate(
            fault_mode="DROPOUT",
            packet_loss_percent=100,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["readings"], [])
        self.assertEqual(
            response.data["run"]["generated_count"],
            0,
        )
        self.assertEqual(
            response.data["run"]["status"],
            "NO_DATA",
        )

    def test_disconnected_mode_creates_run_without_readings(self):
        response = self.simulate(
            fault_mode="DISCONNECTED",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["readings"], [])
        self.assertEqual(
            response.data["run"]["status"],
            "NO_DATA",
        )

    def test_zero_noise_is_rejected(self):
        response = self.simulate(
            fault_mode="NOISE",
            noise_level_percent=0,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            VitalSignReading.objects.filter(
                sensor=self.sensor
            ).count(),
            0,
        )

    def test_zero_packet_loss_is_rejected_for_dropout(self):
        response = self.simulate(
            fault_mode="DROPOUT",
            packet_loss_percent=0,
        )

        self.assertEqual(response.status_code, 400)

    def test_medical_officer_cannot_register_sensor(self):
        self.client.force_authenticate(
            user=self.medical_user
        )

        response = self.client.post(
            self.registration_url,
            {
                "sensor_code": "VS-FORBIDDEN-001",
                "astronaut_id": self.astronaut.id,
                "mission_id": self.mission.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            VirtualHealthSensor.objects.filter(
                sensor_code="VS-FORBIDDEN-001"
            ).exists()
        )

    def test_unauthenticated_sensor_access_is_rejected(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(
            self.registration_url
        )

        self.assertEqual(response.status_code, 401)
