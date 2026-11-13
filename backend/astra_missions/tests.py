from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from astra_accounts.models import UserProfile
from astra_crew.models import Astronaut
from .models import Mission


User = get_user_model()


class MissionAPITests(TestCase):

    def setUp(self):

        self.client = APIClient()

        # Mission Control user
        self.mc_user = User.objects.create_user(
            username="mission_mc",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.mc_user,
            full_name="Test Mission Control",
            role=UserProfile.Role.MISSION_CONTROL
        )

        # First astronaut
        self.astronaut_user = User.objects.create_user(
            username="mission_astronaut_1",
            password="TestPassword123!"
        )

        self.astronaut_profile = UserProfile.objects.create(
            user=self.astronaut_user,
            full_name="Mission Astronaut One",
            role=UserProfile.Role.ASTRONAUT
        )

        self.astronaut = Astronaut.objects.create(
            profile=self.astronaut_profile,
            astronaut_code="MISSION-TEST-001",
            call_sign="MISSION-ONE"
        )

        # Second astronaut
        self.other_user = User.objects.create_user(
            username="mission_astronaut_2",
            password="TestPassword123!"
        )

        self.other_profile = UserProfile.objects.create(
            user=self.other_user,
            full_name="Mission Astronaut Two",
            role=UserProfile.Role.ASTRONAUT
        )

        self.other_astronaut = Astronaut.objects.create(
            profile=self.other_profile,
            astronaut_code="MISSION-TEST-002",
            call_sign="MISSION-TWO"
        )

        self.list_url = reverse("mission-list-create")

        # Mission assigned to first astronaut
        self.assigned_mission = Mission.objects.create(
            mission_code="MISSION-API-001",
            mission_name="Assigned Test Mission",
            mission_type=Mission.MissionType.ORBITAL,
            status=Mission.Status.PLANNED,
            created_by=self.mc_user
        )

        self.assigned_mission.crew.add(self.astronaut)

        # Mission assigned to second astronaut
        self.other_mission = Mission.objects.create(
            mission_code="MISSION-API-002",
            mission_name="Other Test Mission",
            mission_type=Mission.MissionType.LUNAR,
            status=Mission.Status.PLANNED,
            created_by=self.mc_user
        )

        self.other_mission.crew.add(self.other_astronaut)

    def test_mission_control_can_list_all_missions(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_astronaut_can_only_see_assigned_missions(self):

        self.client.force_authenticate(user=self.astronaut_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        self.assertEqual(
            response.data[0]["id"],
            self.assigned_mission.id
        )

    def test_astronaut_cannot_access_unassigned_mission(self):

        self.client.force_authenticate(user=self.astronaut_user)

        url = reverse(
            "mission-detail",
            args=[self.other_mission.id]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_mission_control_can_create_mission(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.post(
            self.list_url,
            {
                "mission_code": "MISSION-API-003",
                "mission_name": "New Orbital Test Mission",
                "mission_type": "ORBITAL",
                "status": "PLANNED",
                "destination": "Low Earth Orbit",
                "description": "Automated regression test mission",
                "crew_ids": [self.astronaut.id]
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)

        self.assertTrue(
            Mission.objects.filter(
                mission_code="MISSION-API-003"
            ).exists()
        )

    def test_mission_creator_is_recorded_correctly(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.post(
            self.list_url,
            {
                "mission_code": "MISSION-API-004",
                "mission_name": "Creator Tracking Test",
                "mission_type": "RESEARCH",
                "status": "PLANNED"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)

        self.assertEqual(
            response.data["created_by"]["id"],
            self.mc_user.id
        )

        self.assertEqual(
            response.data["created_by"]["username"],
            self.mc_user.username
        )

    def test_mission_can_be_assigned_to_astronauts(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.post(
            self.list_url,
            {
                "mission_code": "MISSION-API-005",
                "mission_name": "Crew Assignment Test",
                "mission_type": "ORBITAL",
                "status": "PLANNED",
                "crew_ids": [
                    self.astronaut.id,
                    self.other_astronaut.id
                ]
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)

        created_mission = Mission.objects.get(
            mission_code="MISSION-API-005"
        )

        self.assertEqual(created_mission.crew.count(), 2)

        self.assertEqual(len(response.data["crew"]), 2)

    def test_astronaut_cannot_create_mission(self):

        self.client.force_authenticate(user=self.astronaut_user)

        response = self.client.post(
            self.list_url,
            {
                "mission_code": "MISSION-BLOCKED-001",
                "mission_name": "Unauthorized Mission"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 403)

    def test_medical_officer_cannot_create_mission(self):

        medical_user = User.objects.create_user(
            username="mission_medical",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=medical_user,
            full_name="Test Medical Officer",
            role=UserProfile.Role.MEDICAL_OFFICER
        )

        self.client.force_authenticate(user=medical_user)

        response = self.client.post(
            self.list_url,
            {
                "mission_code": "MISSION-BLOCKED-002",
                "mission_name": "Medical Unauthorized Mission"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 403)

    def test_mission_control_can_update_mission(self):

        self.client.force_authenticate(user=self.mc_user)

        url = reverse(
            "mission-detail",
            args=[self.assigned_mission.id]
        )

        response = self.client.patch(
            url,
            {
                "mission_name": "Updated Mission Name"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        self.assigned_mission.refresh_from_db()

        self.assertEqual(
            self.assigned_mission.mission_name,
            "Updated Mission Name"
        )

    def test_astronaut_cannot_update_mission(self):

        self.client.force_authenticate(user=self.astronaut_user)

        url = reverse(
            "mission-detail",
            args=[self.assigned_mission.id]
        )

        response = self.client.patch(
            url,
            {
                "mission_name": "Unauthorized Update"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 403)

    def test_astronaut_cannot_delete_mission(self):

        self.client.force_authenticate(user=self.astronaut_user)

        url = reverse(
            "mission-detail",
            args=[self.assigned_mission.id]
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Mission.objects.filter(
                id=self.assigned_mission.id
            ).exists()
        )

    def test_mission_end_date_cannot_be_before_start_date(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.post(
            self.list_url,
            {
                "mission_code": "MISSION-INVALID-DATE",
                "mission_name": "Invalid Date Test",
                "mission_type": "ORBITAL",
                "status": "PLANNED",
                "planned_start_date": "2026-12-20",
                "planned_end_date": "2026-12-10"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)

        self.assertFalse(
            Mission.objects.filter(
                mission_code="MISSION-INVALID-DATE"
            ).exists()
        )

    def test_duplicate_mission_code_is_rejected(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.post(
            self.list_url,
            {
                "mission_code": "MISSION-API-001",
                "mission_name": "Duplicate Mission Code Test",
                "mission_type": "ORBITAL",
                "status": "PLANNED"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            Mission.objects.filter(
                mission_code="MISSION-API-001"
            ).count(),
            1
        )


# ==========================================================
# DASHBOARD ANALYTICS API TESTS
# ==========================================================

from django.utils import timezone

from astra_health.models import VitalSignReading
from astra_alerts.models import HealthAlert


class DashboardAnalyticsAPITests(TestCase):

    def setUp(self):

        self.client = APIClient()

        # Mission Control
        self.mc_user = User.objects.create_user(
            username="dashboard_mc",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.mc_user,
            full_name="Dashboard Mission Control",
            role=UserProfile.Role.MISSION_CONTROL
        )

        # First astronaut
        self.astronaut_user = User.objects.create_user(
            username="dashboard_astronaut_1",
            password="TestPassword123!"
        )

        self.astronaut_profile = UserProfile.objects.create(
            user=self.astronaut_user,
            full_name="Dashboard Astronaut One",
            role=UserProfile.Role.ASTRONAUT
        )

        self.astronaut = Astronaut.objects.create(
            profile=self.astronaut_profile,
            astronaut_code="DASH-TEST-001",
            call_sign="DASH-ONE"
        )

        # Second astronaut
        self.other_user = User.objects.create_user(
            username="dashboard_astronaut_2",
            password="TestPassword123!"
        )

        self.other_profile = UserProfile.objects.create(
            user=self.other_user,
            full_name="Dashboard Astronaut Two",
            role=UserProfile.Role.ASTRONAUT
        )

        self.other_astronaut = Astronaut.objects.create(
            profile=self.other_profile,
            astronaut_code="DASH-TEST-002",
            call_sign="DASH-TWO"
        )

        # Medical Officer
        self.medical_user = User.objects.create_user(
            username="dashboard_medical",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.medical_user,
            full_name="Dashboard Medical Officer",
            role=UserProfile.Role.MEDICAL_OFFICER
        )

        # Mission for first astronaut
        self.mission = Mission.objects.create(
            mission_code="DASH-MISSION-001",
            mission_name="Dashboard Test Mission One",
            mission_type=Mission.MissionType.ORBITAL,
            status=Mission.Status.ACTIVE,
            created_by=self.mc_user
        )

        self.mission.crew.add(self.astronaut)

        # Mission for second astronaut
        self.other_mission = Mission.objects.create(
            mission_code="DASH-MISSION-002",
            mission_name="Dashboard Test Mission Two",
            mission_type=Mission.MissionType.LUNAR,
            status=Mission.Status.PLANNED,
            created_by=self.mc_user
        )

        self.other_mission.crew.add(self.other_astronaut)

        self.dashboard_url = reverse("dashboard-analytics")

    def create_reading(
        self,
        astronaut,
        mission=None,
        heart_rate=75,
        data_quality=VitalSignReading.DataQuality.VALID
    ):

        return VitalSignReading.objects.create(
            astronaut=astronaut,
            mission=mission,
            heart_rate_bpm=heart_rate,
            spo2_percent=98,
            body_temperature_c="36.70",
            respiratory_rate_bpm=16,
            recorded_at=timezone.now(),
            data_quality=data_quality,
            data_source=VitalSignReading.DataSource.TEST_FIXTURE
        )

    def create_alert(
        self,
        reading,
        severity=HealthAlert.Severity.WARNING,
        rule_code="DASH_TEST_ALERT"
    ):

        return HealthAlert.objects.create(
            reading=reading,
            severity=severity,
            parameter="heart_rate_bpm",
            rule_code=rule_code,
            observed_value=str(reading.heart_rate_bpm),
            explanation="Synthetic dashboard test alert."
        )

    def test_mission_control_can_access_global_analytics(self):

        reading_one = self.create_reading(
            self.astronaut,
            self.mission
        )

        reading_two = self.create_reading(
            self.other_astronaut,
            self.other_mission
        )

        self.create_alert(
            reading_one,
            HealthAlert.Severity.WARNING,
            "DASH_GLOBAL_WARNING"
        )

        self.create_alert(
            reading_two,
            HealthAlert.Severity.CRITICAL,
            "DASH_GLOBAL_CRITICAL"
        )

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

        self.assertEqual(response.data["crew"]["total"], 2)
        self.assertEqual(response.data["missions"]["total"], 2)

        self.assertEqual(response.data["health"]["total"], 2)
        self.assertEqual(response.data["alerts"]["total"], 2)

        self.assertEqual(
            response.data["data_scope"],
            "AUTHORIZED_GLOBAL_RECORDS"
        )

        self.assertEqual(len(response.data["latest_readings"]), 2)
        self.assertEqual(len(response.data["mission_summary"]), 2)

    def test_astronaut_only_sees_own_dashboard_data(self):

        own_reading = self.create_reading(
            self.astronaut,
            self.mission
        )

        other_reading = self.create_reading(
            self.other_astronaut,
            self.other_mission
        )

        self.create_alert(
            own_reading,
            HealthAlert.Severity.WARNING,
            "DASH_OWN_WARNING"
        )

        self.create_alert(
            other_reading,
            HealthAlert.Severity.CRITICAL,
            "DASH_OTHER_CRITICAL"
        )

        self.client.force_authenticate(
            user=self.astronaut_user
        )

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["crew"]["total"], 1)
        self.assertEqual(response.data["missions"]["total"], 1)
        self.assertEqual(response.data["health"]["total"], 1)
        self.assertEqual(response.data["alerts"]["total"], 1)

        self.assertEqual(
            response.data["data_scope"],
            "OWN_RECORDS"
        )

        self.assertEqual(
            response.data["latest_readings"][0]["astronaut_code"],
            self.astronaut.astronaut_code
        )

        self.assertEqual(
            response.data["mission_summary"][0]["mission_code"],
            self.mission.mission_code
        )

        self.assertNotIn(
            self.other_astronaut.astronaut_code,
            str(response.data)
        )

        self.assertNotIn(
            self.other_mission.mission_code,
            str(response.data)
        )

    def test_non_synthetic_readings_and_alerts_are_excluded(self):

        synthetic_reading = self.create_reading(
            self.astronaut,
            self.mission
        )

        non_synthetic_reading = self.create_reading(
            self.other_astronaut,
            self.other_mission
        )

        VitalSignReading.objects.filter(
            id=non_synthetic_reading.id
        ).update(is_synthetic=False)

        self.create_alert(
            synthetic_reading,
            HealthAlert.Severity.WARNING,
            "DASH_SYNTHETIC_ALERT"
        )

        non_synthetic_alert = self.create_alert(
            non_synthetic_reading,
            HealthAlert.Severity.CRITICAL,
            "DASH_NON_SYNTHETIC_ALERT"
        )

        HealthAlert.objects.filter(
            id=non_synthetic_alert.id
        ).update(is_synthetic=False)

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["health"]["total"], 1)
        self.assertEqual(response.data["alerts"]["total"], 1)

        self.assertEqual(
            len(response.data["latest_readings"]),
            1
        )

        self.assertEqual(
            len(response.data["latest_critical_alerts"]),
            0
        )

    def test_latest_critical_alerts_are_returned(self):

        reading = self.create_reading(
            self.astronaut,
            self.mission,
            heart_rate=160,
            data_quality=VitalSignReading.DataQuality.SUSPECT
        )

        alert = self.create_alert(
            reading,
            HealthAlert.Severity.CRITICAL,
            "DASH_LATEST_CRITICAL"
        )

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.data["latest_critical_alerts"]),
            1
        )

        returned_alert = response.data["latest_critical_alerts"][0]

        self.assertEqual(returned_alert["id"], alert.id)
        self.assertEqual(returned_alert["severity"], "CRITICAL")
        self.assertEqual(
            returned_alert["astronaut_code"],
            self.astronaut.astronaut_code
        )

    def test_medical_officer_can_access_global_analytics(self):

        self.create_reading(
            self.astronaut,
            self.mission
        )

        self.create_reading(
            self.other_astronaut,
            self.other_mission
        )

        self.client.force_authenticate(
            user=self.medical_user
        )

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["crew"]["total"], 2)
        self.assertEqual(response.data["health"]["total"], 2)

        self.assertEqual(
            response.data["data_scope"],
            "AUTHORIZED_GLOBAL_RECORDS"
        )

    def test_empty_health_dataset_returns_zero_counts(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data["health"]["total"], 0)
        self.assertEqual(response.data["alerts"]["total"], 0)

        self.assertEqual(response.data["alerts"]["open"], 0)
        self.assertEqual(response.data["alerts"]["critical"], 0)

        self.assertEqual(response.data["latest_readings"], [])
        self.assertEqual(response.data["latest_critical_alerts"], [])

    def test_unauthenticated_user_cannot_access_dashboard(self):

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 401)

    def test_user_without_profile_cannot_access_dashboard(self):

        user_without_profile = User.objects.create_user(
            username="dashboard_no_profile",
            password="TestPassword123!"
        )

        self.client.force_authenticate(
            user=user_without_profile
        )

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 403)
