from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from astra_accounts.models import UserProfile
from astra_alerts.models import HealthAlert
from astra_crew.models import Astronaut
from astra_health.models import VitalSignReading
from astra_missions.models import Mission
from astra_simulator.models import HabitatTelemetry
from astra_simulator.services.mission_explainability import (
    FINDINGS_LIMIT,
    get_mission_explainability,
)


User = get_user_model()


class MissionExplainabilityAuditTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="xai_audit_test_user",
            password="TestPassword123!",
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name="XAI Audit Astronaut",
            role=UserProfile.Role.ASTRONAUT,
        )

        self.astronaut = Astronaut.objects.create(
            profile=self.profile,
            astronaut_code="XAI-AUDIT-001",
            call_sign="AUDIT-ONE",
        )

        self.mission = Mission.objects.create(
            mission_code="XAI-AUDIT-MISSION",
            mission_name="Explainability Audit Test",
            mission_type=Mission.MissionType.ORBITAL,
            status=Mission.Status.PLANNED,
            created_by=self.user,
        )

        self.recorded_at = timezone.now().replace(microsecond=0)

    def create_reading(self, index=0):
        return VitalSignReading.objects.create(
            astronaut=self.astronaut,
            mission=self.mission,
            heart_rate_bpm=75,
            spo2_percent=98,
            body_temperature_c="36.50",
            respiratory_rate_bpm=16,
            recorded_at=self.recorded_at + timedelta(seconds=index),
        )

    def create_alert(self, index=0, severity=HealthAlert.Severity.WARNING):
        reading = self.create_reading(index=index)

        return HealthAlert.objects.create(
            reading=reading,
            severity=severity,
            parameter="HEART_RATE",
            rule_code=f"XAI_TEST_RULE_{index}",
            observed_value="105.00",
            explanation="Persisted test alert explanation.",
            status=HealthAlert.Status.OPEN,
        )

    def create_habitat(
        self,
        index=0,
        quality=HabitatTelemetry.DataQuality.SUSPECT,
    ):
        return HabitatTelemetry.objects.create(
            mission=self.mission,
            sensor_id=f"XAI-SENSOR-{index}",
            oxygen_partial_pressure_kpa="21.00",
            carbon_dioxide_ppm=1200,
            cabin_pressure_kpa="101.30",
            cabin_temperature_c="22.00",
            relative_humidity_percent="45.00",
            scenario="ELEVATED_CO2",
            data_quality=quality,
            recorded_at=self.recorded_at + timedelta(seconds=index),
        )

    def test_empty_mission_returns_zeroed_audit(self):
        result = get_mission_explainability(self.mission)

        audit = result["audit_summary"]

        self.assertEqual(
            audit["source_counts"],
            {
                "crew_health_alerts": 0,
                "habitat_telemetry": 0,
            },
        )

        self.assertEqual(
            audit["record_counts"],
            {
                "total_evidence_records": 0,
                "synthetic_records": 0,
                "non_synthetic_records": 0,
            },
        )

        self.assertEqual(
            result["mission_assessment"]["code"],
            "NO_FLAGGED_EVIDENCE",
        )

    def test_audit_counts_unique_source_records_and_synthetic_status(self):
        first_alert = self.create_alert(index=1)
        self.create_alert(index=2)

        habitat = self.create_habitat(index=1)

        HealthAlert.objects.filter(pk=first_alert.pk).update(
            is_synthetic=False,
        )

        HabitatTelemetry.objects.filter(pk=habitat.pk).update(
            is_synthetic=False,
        )

        result = get_mission_explainability(self.mission)
        audit = result["audit_summary"]

        self.assertEqual(
            audit["source_counts"]["crew_health_alerts"],
            2,
        )
        self.assertEqual(
            audit["source_counts"]["habitat_telemetry"],
            1,
        )

        self.assertEqual(
            audit["record_counts"]["total_evidence_records"],
            3,
        )
        self.assertEqual(
            audit["record_counts"]["synthetic_records"],
            1,
        )
        self.assertEqual(
            audit["record_counts"]["non_synthetic_records"],
            2,
        )

        self.assertIn(
            "VitalSignReading references are not counted separately",
            audit["record_scope"],
        )

    def test_crew_alert_findings_preserve_source_traceability(self):
        alert = self.create_alert(
            index=3,
            severity=HealthAlert.Severity.CRITICAL,
        )

        result = get_mission_explainability(self.mission)

        finding = result["crew_findings"]["items"][0]

        self.assertEqual(
            finding["source"],
            "CREW_HEALTH_ALERT",
        )
        self.assertEqual(
            finding["source_record_id"],
            alert.pk,
        )
        self.assertEqual(
            finding["reading_id"],
            alert.reading_id,
        )
        self.assertEqual(
            finding["astronaut_code"],
            self.astronaut.astronaut_code,
        )
        self.assertEqual(
            finding["astronaut_name"],
            self.profile.full_name,
        )
        self.assertEqual(
            finding["evidence_type"],
            "PERSISTED_ALERT_EXPLANATION",
        )

    def test_suspect_habitat_finding_preserves_sensor_traceability(self):
        habitat = self.create_habitat(
            index=4,
            quality=HabitatTelemetry.DataQuality.SUSPECT,
        )

        result = get_mission_explainability(self.mission)

        finding = result["habitat_findings"]["items"][0]

        self.assertEqual(
            finding["source"],
            "HABITAT_TELEMETRY",
        )
        self.assertEqual(
            finding["source_record_id"],
            habitat.pk,
        )
        self.assertEqual(
            finding["sensor_id"],
            habitat.sensor_id,
        )
        self.assertEqual(
            finding["data_quality"],
            HabitatTelemetry.DataQuality.SUSPECT,
        )
        self.assertEqual(
            finding["evidence_type"],
            "SYNTHETIC_SCENARIO_METADATA",
        )

        self.assertEqual(
            result["mission_assessment"]["code"],
            "SUSPECT_HABITAT_DATA",
        )

    def test_ungradable_habitat_is_counted_but_never_interpreted(self):
        self.create_habitat(
            index=5,
            quality=HabitatTelemetry.DataQuality.UNGRADABLE,
        )

        result = get_mission_explainability(self.mission)

        self.assertEqual(
            result["habitat_findings"]["quality_counts"]["UNGRADABLE"],
            1,
        )
        self.assertEqual(
            result["habitat_findings"]["returned_count"],
            0,
        )
        self.assertEqual(
            result["habitat_findings"]["items"],
            [],
        )
        self.assertEqual(
            result["mission_assessment"]["code"],
            "DATA_QUALITY_REVIEW",
        )

        self.assertEqual(
            result["audit_summary"]["record_counts"]["total_evidence_records"],
            1,
        )

    def test_findings_limit_and_truncation_are_accurate(self):
        for index in range(FINDINGS_LIMIT + 1):
            self.create_alert(index=100 + index)

        result = get_mission_explainability(self.mission)

        retrieval = result["audit_summary"]["retrieval"]["crew_findings"]

        self.assertEqual(
            retrieval["available"],
            FINDINGS_LIMIT + 1,
        )
        self.assertEqual(
            retrieval["returned"],
            FINDINGS_LIMIT,
        )
        self.assertEqual(
            retrieval["limit"],
            FINDINGS_LIMIT,
        )
        self.assertTrue(retrieval["truncated"])

        self.assertEqual(
            result["crew_findings"]["returned_count"],
            FINDINGS_LIMIT,
        )
