from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from astra_accounts.models import UserProfile
from astra_crew.models import Astronaut
from astra_health.models import VitalSignReading
from astra_health.ai.predictive_analytics import get_predictive_analytics


User = get_user_model()


class PredictiveAnalyticsDatabaseTests(TestCase):

    def setUp(self):
        user = User.objects.create_user(
            username="predictive_db_astronaut",
            password="TestPassword123!"
        )

        profile = UserProfile.objects.create(
            user=user,
            full_name="Predictive Database Astronaut",
            role=UserProfile.Role.ASTRONAUT,
        )

        self.astronaut = Astronaut.objects.create(
            profile=profile,
            astronaut_code="PREDICTIVE-DB-001",
            call_sign="PREDICTIVE-ONE",
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
            heart_rate_bpm=80,
            spo2_percent=98,
            body_temperature_c="36.70",
            respiratory_rate_bpm=15,
            recorded_at=self.now,
            data_quality=VitalSignReading.DataQuality.VALID,
            data_source=VitalSignReading.DataSource.SIMULATOR,
            is_synthetic=True,
        )

    def test_database_history_generates_trend(self):

        result = get_predictive_analytics(self.current)

        self.assertEqual(
            result["status"],
            "TREND_ESTIMATED",
        )

        self.assertEqual(
            result["historical_readings"],
            12,
        )

        self.assertEqual(
            result["astronaut_id"],
            self.astronaut.id,
        )

        self.assertFalse(
            result["clinical_validation"]
        )

    def test_current_reading_is_not_in_its_own_history(self):

        result = get_predictive_analytics(self.current)

        eligible_ids = VitalSignReading.objects.filter(
            astronaut=self.astronaut,
            recorded_at__lt=self.current.recorded_at,
            is_synthetic=True,
            data_quality=VitalSignReading.DataQuality.VALID,
        ).values_list("id", flat=True)

        self.assertEqual(result["historical_readings"], 12)
        self.assertNotIn(self.current.id, eligible_ids)
        self.assertEqual(
            result["historical_readings"],
            eligible_ids.count(),
        )

    def test_other_astronaut_readings_are_excluded(self):

        user = User.objects.create_user(
            username="predictive_other_astronaut",
            password="TestPassword123!"
        )

        profile = UserProfile.objects.create(
            user=user,
            full_name="Other Astronaut",
            role=UserProfile.Role.ASTRONAUT,
        )

        other_astronaut = Astronaut.objects.create(
            profile=profile,
            astronaut_code="PREDICTIVE-DB-002",
            call_sign="PREDICTIVE-TWO",
        )

        VitalSignReading.objects.filter(
            astronaut=self.astronaut
        ).delete()

        for index in range(12):
            variation = (index % 3) - 1

            VitalSignReading.objects.create(
                astronaut=other_astronaut,
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

        result = get_predictive_analytics(self.current)

        self.assertEqual(
            result["status"],
            "INSUFFICIENT_DATA",
        )

        self.assertEqual(
            result["historical_readings"],
            0,
        )

    def test_suspect_and_ungradable_history_are_excluded(self):

        historical = list(
            VitalSignReading.objects.filter(
                astronaut=self.astronaut
            )
        )

        for index, item in enumerate(historical):
            if index % 2 == 0:
                item.data_quality = VitalSignReading.DataQuality.SUSPECT
            else:
                item.data_quality = VitalSignReading.DataQuality.UNGRADABLE

        VitalSignReading.objects.bulk_update(
            historical,
            ["data_quality"],
        )

        result = get_predictive_analytics(self.current)

        self.assertEqual(result["status"], "INSUFFICIENT_DATA")
        self.assertEqual(result["historical_readings"], 0)

    def test_history_older_than_30_days_is_excluded(self):

        VitalSignReading.objects.filter(
            astronaut=self.astronaut
        ).update(
            recorded_at=self.now - timedelta(days=31)
        )

        result = get_predictive_analytics(self.current)

        self.assertEqual(
            result["status"],
            "INSUFFICIENT_DATA",
        )

        self.assertEqual(
            result["historical_readings"],
            0,
        )

    def test_non_synthetic_current_does_not_query_database(self):

        self.current.is_synthetic = False

        with self.assertNumQueries(0):
            result = get_predictive_analytics(self.current)

        self.assertEqual(
            result["status"],
            "NOT_EVALUATED",
        )
