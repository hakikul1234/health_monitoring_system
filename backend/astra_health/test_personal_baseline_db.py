from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from django.contrib.auth import get_user_model

from astra_accounts.models import UserProfile
from astra_crew.models import Astronaut
from astra_health.models import VitalSignReading
from astra_health.ai.personal_baseline import get_personal_baseline


User = get_user_model()


class PersonalBaselineDatabaseTests(TestCase):

    def setUp(self):
        user = User.objects.create_user(
            username="baseline_db_astronaut",
            password="TestPassword123!"
        )

        profile = UserProfile.objects.create(
            user=user,
            full_name="Baseline Database Astronaut",
            role=UserProfile.Role.ASTRONAUT,
        )

        self.astronaut = Astronaut.objects.create(
            profile=profile,
            astronaut_code="BASELINE-DB-001",
            call_sign="BASELINE-ONE",
        )

        self.now = timezone.now()

        for index in range(12):
            variation = (index % 3) - 1

            VitalSignReading.objects.create(
                astronaut=self.astronaut,
                heart_rate_bpm=75 + variation,
                spo2_percent=98 + variation,
                body_temperature_c=36.70 + (variation * 0.10),
                respiratory_rate_bpm=15 + variation,
                recorded_at=self.now - timedelta(
                    minutes=(index + 1) * 10
                ),
                data_quality=VitalSignReading.DataQuality.VALID,
                data_source=VitalSignReading.DataSource.SIMULATOR,
                is_synthetic=True,
            )

        self.current = VitalSignReading.objects.create(
            astronaut=self.astronaut,
            heart_rate_bpm=150,
            spo2_percent=98,
            body_temperature_c="36.70",
            respiratory_rate_bpm=15,
            recorded_at=self.now,
            data_quality=VitalSignReading.DataQuality.VALID,
            data_source=VitalSignReading.DataSource.SIMULATOR,
            is_synthetic=True,
        )

    def test_database_history_generates_personal_baseline(self):

        result = get_personal_baseline(self.current)

        self.assertEqual(
            result["status"],
            "DEVIATION",
        )

        self.assertEqual(
            result["baseline_readings"],
            12,
        )

        self.assertTrue(
            result["features"]["heart_rate_bpm"]["deviation_detected"]
        )

    def test_current_reading_is_not_in_its_own_baseline(self):

        result = get_personal_baseline(self.current)

        self.assertEqual(
            result["baseline_readings"],
            12,
        )

    def test_ungradable_reading_does_not_query_baseline(self):

        self.current.data_quality = (
            VitalSignReading.DataQuality.UNGRADABLE
        )

        self.current.save(update_fields=["data_quality"])

        result = get_personal_baseline(self.current)

        self.assertEqual(
            result["status"],
            "INSUFFICIENT_DATA",
        )

        self.assertEqual(
            result["baseline_readings"],
            0,
        )
