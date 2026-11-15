from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from astra_accounts.models import UserProfile
from astra_crew.models import Astronaut
from astra_health.models import (
    SensorSimulationRun,
    VirtualHealthSensor,
    VitalSignReading,
)
from astra_missions.models import Mission
from astra_simulator.services.trust_decision_engine import (
    evaluate_reading_trust,
)


User = get_user_model()


class TrustDecisionEngineTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="trust_engine_mc",
            password="TestPassword123!",
        )

        self.profile = UserProfile.objects.create(
            user=self.user,
            full_name="Trust Engine Test Astronaut",
            role=UserProfile.Role.ASTRONAUT,
        )

        self.astronaut = Astronaut.objects.create(
            profile=self.profile,
            astronaut_code="TRUST-TEST-001",
            call_sign="TRUST-ONE",
        )

        self.mission_user = User.objects.create_user(
            username="trust_engine_admin",
            password="TestPassword123!",
        )

        self.mission = Mission.objects.create(
            mission_code="TRUST-TEST-MISSION",
            mission_name="Trust Engine Test Mission",
            mission_type=Mission.MissionType.ORBITAL,
            status=Mission.Status.PLANNED,
            created_by=self.mission_user,
        )

        self.mission.crew.add(self.astronaut)

        self.sensor = self.make_sensor("TRUST-SENSOR-001")
        self.run = self.make_run(self.sensor)

        self.reading = self.make_reading(
            self.sensor,
            self.run,
        )

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

    def make_sensor(self, code, astronaut=None, status=None):
        return VirtualHealthSensor.objects.create(
            sensor_code=code,
            astronaut=astronaut or self.astronaut,
            mission=self.mission,
            status=status or VirtualHealthSensor.SensorStatus.ACTIVE,
            manufacturer="ASTRA Test Systems",
            model_number="TRUST-TEST",
            firmware_version="1.0.0",
        )

    def make_run(
        self,
        sensor,
        fault_mode=SensorSimulationRun.FaultMode.NORMAL,
        status=SensorSimulationRun.RunStatus.COMPLETED,
    ):
        return SensorSimulationRun.objects.create(
            sensor=sensor,
            fault_mode=fault_mode,
            status=status,
            requested_count=1,
            generated_count=1,
            completed_at=timezone.now(),
        )

    def make_reading(
        self,
        sensor,
        run,
        data_quality=VitalSignReading.DataQuality.VALID,
        data_source=VitalSignReading.DataSource.SIMULATOR,
        astronaut=None,
        is_synthetic=True,
    ):
        return VitalSignReading.objects.create(
            astronaut=astronaut or self.astronaut,
            mission=self.mission,
            sensor=sensor,
            simulation_run=run,
            heart_rate_bpm=75,
            spo2_percent=98,
            body_temperature_c="36.80",
            respiratory_rate_bpm=16,
            recorded_at=timezone.now(),
            data_quality=data_quality,
            data_source=data_source,
            is_synthetic=is_synthetic,
        )

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_clean_reading_is_accepted(self, detector):
        detector.return_value = self.normal_analysis

        result = evaluate_reading_trust(self.reading)

        self.assertEqual(result["decision"], "ACCEPT")
        self.assertEqual(
            result["reason_code"],
            "QUALITY_AND_PROVENANCE_CHECKS_PASSED",
        )

    def test_suspect_reading_requires_remeasurement(self):
        self.reading.data_quality = VitalSignReading.DataQuality.SUSPECT
        self.reading.save()

        result = evaluate_reading_trust(self.reading)

        self.assertEqual(result["decision"], "REMEASURE")
        self.assertEqual(result["reason_code"], "READING_MARKED_SUSPECT")

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_degraded_sensor_requires_remeasurement(self, detector):
        self.sensor.status = VirtualHealthSensor.SensorStatus.DEGRADED
        self.sensor.save()

        result = evaluate_reading_trust(self.reading)

        self.assertEqual(result["decision"], "REMEASURE")
        detector.assert_not_called()

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_fault_injected_run_requires_remeasurement(self, detector):
        self.run.fault_mode = SensorSimulationRun.FaultMode.NOISE
        self.run.save()

        result = evaluate_reading_trust(self.reading)

        self.assertEqual(result["decision"], "REMEASURE")
        self.assertEqual(result["reason_code"], "SIMULATED_SENSOR_FAULT")
        detector.assert_not_called()

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_ungradable_reading_abstains_without_analysis(self, detector):
        self.reading.data_quality = VitalSignReading.DataQuality.UNGRADABLE
        self.reading.heart_rate_bpm = 999
        self.reading.save()

        result = evaluate_reading_trust(self.reading)

        self.assertEqual(result["decision"], "ABSTAIN")
        self.assertEqual(result["reason_code"], "READING_UNGRADABLE")
        detector.assert_not_called()

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_non_synthetic_reading_abstains(self, detector):
        self.reading.is_synthetic = False
        self.reading.save()

        result = evaluate_reading_trust(self.reading)

        self.assertEqual(result["decision"], "ABSTAIN")
        self.assertEqual(
            result["reason_code"],
            "NON_SYNTHETIC_DATA_NOT_EVALUATED",
        )
        detector.assert_not_called()

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_missing_sensor_abstains(self, detector):
        self.reading.sensor = None
        self.reading.save()

        result = evaluate_reading_trust(self.reading)

        self.assertEqual(result["decision"], "ABSTAIN")
        self.assertEqual(result["reason_code"], "SENSOR_REFERENCE_MISSING")
        detector.assert_not_called()

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_disconnected_sensor_abstains(self, detector):
        self.sensor.status = VirtualHealthSensor.SensorStatus.DISCONNECTED
        self.sensor.save()

        result = evaluate_reading_trust(self.reading)

        self.assertEqual(result["decision"], "ABSTAIN")
        self.assertEqual(result["reason_code"], "SENSOR_DISCONNECTED")
        detector.assert_not_called()

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_incomplete_simulation_run_abstains(self, detector):
        self.run.status = SensorSimulationRun.RunStatus.PARTIAL
        self.run.save()

        result = evaluate_reading_trust(self.reading)

        self.assertEqual(result["decision"], "ABSTAIN")
        self.assertEqual(result["reason_code"], "SIMULATION_RUN_INCOMPLETE")
        detector.assert_not_called()

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_anomaly_with_independent_sensor_returns_cross_check(self, detector):
        second_sensor = self.make_sensor("TRUST-SENSOR-002")
        second_run = self.make_run(second_sensor)
        second_reading = self.make_reading(second_sensor, second_run)

        detector.side_effect = [
            self.anomalous_analysis,
            self.normal_analysis,
        ]

        result = evaluate_reading_trust(
            self.reading,
            cross_check_reading=second_reading,
        )

        self.assertEqual(result["decision"], "CROSS_CHECK")
        self.assertFalse(
            result["evidence"]["independent_reading"]["comparison_performed"]
        )
        self.assertEqual(
            result["reason_code"],
            "ANOMALY_WITH_INDEPENDENT_EVIDENCE",
        )

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_anomaly_without_independent_sensor_requires_remeasurement(
        self,
        detector,
    ):
        detector.return_value = self.anomalous_analysis

        result = evaluate_reading_trust(self.reading)

        self.assertEqual(result["decision"], "REMEASURE")
        self.assertEqual(
            result["reason_code"],
            "ANOMALY_REQUIRES_VERIFICATION",
        )

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_same_sensor_cannot_be_independent_evidence(self, detector):
        second_run = self.make_run(self.sensor)
        second_reading = self.make_reading(self.sensor, second_run)

        detector.return_value = self.anomalous_analysis

        result = evaluate_reading_trust(
            self.reading,
            cross_check_reading=second_reading,
        )

        self.assertEqual(result["decision"], "REMEASURE")
        self.assertEqual(
            result["cross_check_unavailable_reason"],
            "SAME_SENSOR_NOT_INDEPENDENT",
        )

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_unknown_analysis_status_abstains(self, detector):
        detector.return_value = {
            "status": "UNKNOWN",
            "is_anomalous": False,
            "findings": [],
        }

        result = evaluate_reading_trust(self.reading)

        self.assertEqual(result["decision"], "ABSTAIN")
        self.assertEqual(result["reason_code"], "UNKNOWN_ANALYSIS_STATUS")

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_contradictory_analysis_result_abstains(self, detector):
        detector.return_value = {
            "status": "NORMAL",
            "is_anomalous": True,
            "findings": [{"rule": "CONTRADICTION"}],
        }

        result = evaluate_reading_trust(self.reading)

        self.assertEqual(result["decision"], "ABSTAIN")
        self.assertEqual(
            result["reason_code"],
            "CONTRADICTORY_ANALYSIS_RESULT",
        )

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_faulty_independent_run_is_not_accepted_for_cross_check(
        self,
        detector,
    ):
        second_sensor = self.make_sensor("TRUST-SENSOR-003")
        second_run = self.make_run(
            second_sensor,
            fault_mode=SensorSimulationRun.FaultMode.NOISE,
        )
        second_reading = self.make_reading(second_sensor, second_run)

        detector.return_value = self.anomalous_analysis

        result = evaluate_reading_trust(
            self.reading,
            cross_check_reading=second_reading,
        )

        self.assertEqual(result["decision"], "REMEASURE")
        self.assertEqual(
            result["cross_check_unavailable_reason"],
            "INDEPENDENT_SIMULATED_SENSOR_FAULT",
        )

    @patch(
        "astra_simulator.services.trust_decision_engine.detect_reading_anomalies"
    )
    def test_simulation_sensor_link_mismatch_abstains(self, detector):
        second_sensor = self.make_sensor("TRUST-SENSOR-004")
        self.reading.simulation_run = self.make_run(second_sensor)
        self.reading.save()

        result = evaluate_reading_trust(self.reading)

        self.assertEqual(result["decision"], "ABSTAIN")
        self.assertEqual(
            result["reason_code"],
            "SIMULATION_SENSOR_LINK_MISMATCH",
        )
        detector.assert_not_called()
