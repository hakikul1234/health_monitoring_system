from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient

from astra_accounts.models import UserProfile
from astra_crew.models import Astronaut
from astra_health.models import VitalSignReading

from .models import HealthAlert


User = get_user_model()


class HealthAlertAPITests(TestCase):

    def setUp(self):

        self.client = APIClient()

        # Mission Control user
        self.user = User.objects.create_user(
            username="test_mission_control",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.user,
            full_name="Test Mission Control",
            role=UserProfile.Role.MISSION_CONTROL
        )

        self.client.force_authenticate(user=self.user)

        # Astronaut user and profile
        self.astronaut_user = User.objects.create_user(
            username="test_astronaut",
            password="TestPassword123!"
        )

        self.astronaut_profile = UserProfile.objects.create(
            user=self.astronaut_user,
            full_name="Test Synthetic Astronaut",
            role=UserProfile.Role.ASTRONAUT
        )

        self.astronaut = Astronaut.objects.create(
            profile=self.astronaut_profile,
            astronaut_code="TEST-ASTRA-001",
            call_sign="TEST-ONE"
        )

        # Synthetic health reading
        self.reading = VitalSignReading.objects.create(
            astronaut=self.astronaut,
            heart_rate_bpm=120,
            spo2_percent=93,
            body_temperature_c="37.80",
            respiratory_rate_bpm=28,
            recorded_at=timezone.now(),
            data_quality=VitalSignReading.DataQuality.SUSPECT,
            data_source=VitalSignReading.DataSource.TEST_FIXTURE
        )

        # Synthetic alert
        self.alert = HealthAlert.objects.create(
            reading=self.reading,
            severity=HealthAlert.Severity.WARNING,
            parameter="respiratory_rate_bpm",
            rule_code="TEST_RR_HIGH",
            observed_value="28.00",
            explanation="Synthetic test respiratory-rate anomaly."
        )

    def test_authenticated_user_can_list_alerts(self):

        response = self.client.get(
            reverse("alert-list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_authenticated_user_can_view_alert_detail(self):

        response = self.client.get(
            reverse("alert-detail", args=[self.alert.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.alert.id)

    def test_open_alert_can_be_acknowledged(self):

        response = self.client.post(
            reverse("alert-acknowledge", args=[self.alert.id])
        )

        self.alert.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.alert.status,
            HealthAlert.Status.ACKNOWLEDGED
        )
        self.assertEqual(self.alert.acknowledged_by, self.user)
        self.assertIsNotNone(self.alert.acknowledged_at)

    def test_acknowledgement_records_correct_user(self):

        self.client.post(
            reverse("alert-acknowledge", args=[self.alert.id])
        )

        self.alert.refresh_from_db()

        self.assertEqual(
            self.alert.acknowledged_by_id,
            self.user.id
        )

    def test_already_acknowledged_alert_cannot_be_acknowledged_again(self):

        self.alert.status = HealthAlert.Status.ACKNOWLEDGED
        self.alert.acknowledged_by = self.user
        self.alert.acknowledged_at = timezone.now()
        self.alert.save()

        response = self.client.post(
            reverse("alert-acknowledge", args=[self.alert.id])
        )

        self.assertEqual(response.status_code, 409)

    def test_acknowledged_alert_can_be_resolved(self):

        self.alert.status = HealthAlert.Status.ACKNOWLEDGED
        self.alert.acknowledged_by = self.user
        self.alert.acknowledged_at = timezone.now()
        self.alert.save()

        notes = "Synthetic anomaly reviewed for testing."

        response = self.client.post(
            reverse("alert-resolve", args=[self.alert.id]),
            {"resolution_notes": notes},
            format="json"
        )

        self.alert.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.alert.status,
            HealthAlert.Status.RESOLVED
        )
        self.assertEqual(self.alert.resolved_by, self.user)
        self.assertEqual(self.alert.resolution_notes, notes)
        self.assertIsNotNone(self.alert.resolved_at)

    def test_resolution_notes_are_persisted(self):

        self.alert.status = HealthAlert.Status.ACKNOWLEDGED
        self.alert.save()

        notes = "Test resolution notes."

        self.client.post(
            reverse("alert-resolve", args=[self.alert.id]),
            {"resolution_notes": notes},
            format="json"
        )

        self.alert.refresh_from_db()

        self.assertEqual(self.alert.resolution_notes, notes)

    def test_open_alert_cannot_be_resolved_directly(self):

        response = self.client.post(
            reverse("alert-resolve", args=[self.alert.id]),
            {"resolution_notes": "Attempted direct resolution."},
            format="json"
        )

        self.assertEqual(response.status_code, 409)

        self.alert.refresh_from_db()

        self.assertEqual(
            self.alert.status,
            HealthAlert.Status.OPEN
        )

    def test_empty_resolution_notes_are_rejected(self):

        self.alert.status = HealthAlert.Status.ACKNOWLEDGED
        self.alert.save()

        response = self.client.post(
            reverse("alert-resolve", args=[self.alert.id]),
            {"resolution_notes": "   "},
            format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_statistics_endpoint_returns_correct_counts(self):

        response = self.client.get(
            reverse("alert-statistics")
        )

        self.assertEqual(response.status_code, 200)

        statistics = response.data["statistics"]

        self.assertEqual(statistics["total_alerts"], 1)
        self.assertEqual(statistics["open_alerts"], 1)
        self.assertEqual(statistics["acknowledged_alerts"], 0)
        self.assertEqual(statistics["resolved_alerts"], 0)
        self.assertEqual(statistics["warning_alerts"], 1)
        self.assertEqual(statistics["critical_alerts"], 0)
