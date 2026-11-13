from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from astra_accounts.models import UserProfile
from .models import Astronaut


User = get_user_model()


class AstronautAPITests(TestCase):

    def setUp(self):

        self.client = APIClient()

        # Mission Control
        self.mc_user = User.objects.create_user(
            username="crew_mc",
            password="TestPassword123!"
        )

        UserProfile.objects.create(
            user=self.mc_user,
            full_name="Test Mission Control",
            role=UserProfile.Role.MISSION_CONTROL
        )

        # Astronaut 1
        self.astronaut_user = User.objects.create_user(
            username="crew_astronaut_1",
            password="TestPassword123!"
        )

        self.astronaut_profile = UserProfile.objects.create(
            user=self.astronaut_user,
            full_name="Astronaut One",
            role=UserProfile.Role.ASTRONAUT
        )

        self.astronaut = Astronaut.objects.create(
            profile=self.astronaut_profile,
            astronaut_code="CREW-TEST-001",
            call_sign="TEST-ONE"
        )

        # Astronaut 2
        self.other_user = User.objects.create_user(
            username="crew_astronaut_2",
            password="TestPassword123!"
        )

        self.other_profile = UserProfile.objects.create(
            user=self.other_user,
            full_name="Astronaut Two",
            role=UserProfile.Role.ASTRONAUT
        )

        self.other_astronaut = Astronaut.objects.create(
            profile=self.other_profile,
            astronaut_code="CREW-TEST-002",
            call_sign="TEST-TWO"
        )

        self.list_url = reverse("astronaut-list-create")

    def test_mission_control_can_list_astronauts(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_astronaut_can_only_see_own_record(self):

        self.client.force_authenticate(user=self.astronaut_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.astronaut.id
        )

    def test_astronaut_cannot_access_another_astronaut_detail(self):

        self.client.force_authenticate(user=self.astronaut_user)

        url = reverse(
            "astronaut-detail",
            args=[self.other_astronaut.id]
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_mission_control_can_create_astronaut(self):

        self.client.force_authenticate(user=self.mc_user)

        new_user = User.objects.create_user(
            username="crew_new_astronaut",
            password="TestPassword123!"
        )

        new_profile = UserProfile.objects.create(
            user=new_user,
            full_name="New Test Astronaut",
            role=UserProfile.Role.ASTRONAUT
        )

        response = self.client.post(
            self.list_url,
            {
                "profile_id": new_profile.id,
                "astronaut_code": "CREW-TEST-003",
                "call_sign": "TEST-THREE",
                "status": "TRAINING"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            Astronaut.objects.filter(
                astronaut_code="CREW-TEST-003"
            ).exists()
        )

    def test_astronaut_cannot_create_astronaut(self):

        self.client.force_authenticate(user=self.astronaut_user)

        response = self.client.post(
            self.list_url,
            {
                "profile_id": self.other_profile.id,
                "astronaut_code": "CREW-TEST-004",
                "call_sign": "BLOCKED"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 403)

    def test_medical_officer_cannot_create_astronaut(self):

        medical_user = User.objects.create_user(
            username="crew_medical",
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
                "profile_id": self.other_profile.id,
                "astronaut_code": "CREW-TEST-005"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 403)

    def test_duplicate_astronaut_profile_is_rejected(self):

        self.client.force_authenticate(user=self.mc_user)

        response = self.client.post(
            self.list_url,
            {
                "profile_id": self.astronaut_profile.id,
                "astronaut_code": "CREW-DUPLICATE-001"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 400)

    def test_mission_control_can_update_astronaut(self):

        self.client.force_authenticate(user=self.mc_user)

        url = reverse(
            "astronaut-detail",
            args=[self.astronaut.id]
        )

        response = self.client.patch(
            url,
            {"call_sign": "UPDATED-CALLSIGN"},
            format="json"
        )

        self.assertEqual(response.status_code, 200)

        self.astronaut.refresh_from_db()

        self.assertEqual(
            self.astronaut.call_sign,
            "UPDATED-CALLSIGN"
        )

    def test_astronaut_cannot_update_own_record(self):

        self.client.force_authenticate(user=self.astronaut_user)

        url = reverse(
            "astronaut-detail",
            args=[self.astronaut.id]
        )

        response = self.client.patch(
            url,
            {"call_sign": "UNAUTHORIZED-UPDATE"},
            format="json"
        )

        self.assertEqual(response.status_code, 403)

    def test_astronaut_cannot_delete_own_record(self):

        self.client.force_authenticate(user=self.astronaut_user)

        url = reverse(
            "astronaut-detail",
            args=[self.astronaut.id]
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)

        self.assertTrue(
            Astronaut.objects.filter(
                id=self.astronaut.id
            ).exists()
        )
