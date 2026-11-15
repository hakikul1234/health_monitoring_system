from astra_health.ai.anomaly_detector import detect_reading_anomalies
from astra_health.models import (
    SensorSimulationRun,
    VirtualHealthSensor,
    VitalSignReading,
)


DECISIONS = {
    "ACCEPT": "ACCEPT",
    "REMEASURE": "REMEASURE",
    "CROSS_CHECK": "CROSS_CHECK",
    "ABSTAIN": "ABSTAIN",
}


def _result(decision, reason_code, explanation, next_action, **extra):
    result = {
        "engine": "ASTRA_TRUST_AWARE_DECISION_ENGINE",
        "engine_version": "1.1.0",
        "decision": decision,
        "reason_code": reason_code,
        "explanation": explanation,
        "next_action": next_action,
        "evidence": {},
        "medical_disclaimer": (
            "Software decision-support demonstration only. "
            "Not a medical diagnosis, treatment recommendation, "
            "or spacecraft safety determination."
        ),
    }
    result.update(extra)
    return result


def _validate_sensor_and_run(reading, evidence_label):
    """
    Validate synthetic provenance, sensor ownership/state and,
    when present, simulation-run integrity.

    Returns (error_code, decision) or (None, None).
    """

    sensor = reading.sensor

    if sensor is None:
        return "SENSOR_REFERENCE_MISSING", DECISIONS["ABSTAIN"]

    if not sensor.is_synthetic:
        return "NON_SYNTHETIC_SENSOR_NOT_EVALUATED", DECISIONS["ABSTAIN"]

    if sensor.astronaut_id != reading.astronaut_id:
        return "SENSOR_CREW_MISMATCH", DECISIONS["ABSTAIN"]

    if sensor.status == VirtualHealthSensor.SensorStatus.DISCONNECTED:
        return "SENSOR_DISCONNECTED", DECISIONS["ABSTAIN"]

    if sensor.status == VirtualHealthSensor.SensorStatus.DEGRADED:
        return "SENSOR_MARKED_DEGRADED", DECISIONS["REMEASURE"]

    if sensor.status != VirtualHealthSensor.SensorStatus.ACTIVE:
        return "UNKNOWN_SENSOR_STATE", DECISIONS["ABSTAIN"]

    run = reading.simulation_run

    if run is None:
        if reading.data_source == VitalSignReading.DataSource.SIMULATOR:
            return "SIMULATION_RUN_REFERENCE_MISSING", DECISIONS["ABSTAIN"]
        return None, None

    if run.sensor_id != sensor.id:
        return "SIMULATION_SENSOR_LINK_MISMATCH", DECISIONS["ABSTAIN"]

    if not run.is_synthetic:
        return "NON_SYNTHETIC_SIMULATION_RUN", DECISIONS["ABSTAIN"]

    if run.fault_mode == SensorSimulationRun.FaultMode.DISCONNECTED:
        return "SIMULATED_SENSOR_DISCONNECTION", DECISIONS["ABSTAIN"]

    if run.fault_mode in (
        SensorSimulationRun.FaultMode.NOISE,
        SensorSimulationRun.FaultMode.DRIFT,
        SensorSimulationRun.FaultMode.DROPOUT,
    ):
        return "SIMULATED_SENSOR_FAULT", DECISIONS["REMEASURE"]

    if run.fault_mode != SensorSimulationRun.FaultMode.NORMAL:
        return "UNKNOWN_SIMULATION_FAULT_MODE", DECISIONS["ABSTAIN"]

    if run.status != SensorSimulationRun.RunStatus.COMPLETED:
        return "SIMULATION_RUN_INCOMPLETE", DECISIONS["ABSTAIN"]

    return None, None


def _independent_evidence(reading, candidate):
    """
    Validate a separate synthetic sensor reading for the same astronaut.

    This establishes availability of independent evidence only.
    It does not compare values or establish agreement.
    """

    if candidate is None:
        return None, "NO_INDEPENDENT_READING_SUPPLIED"

    if candidate.pk == reading.pk:
        return None, "SAME_READING_NOT_INDEPENDENT"

    if candidate.astronaut_id != reading.astronaut_id:
        return None, "DIFFERENT_ASTRONAUT"

    if not candidate.is_synthetic:
        return None, "NON_SYNTHETIC_EVIDENCE_NOT_EVALUATED"

    if candidate.data_quality != VitalSignReading.DataQuality.VALID:
        return None, "INDEPENDENT_READING_NOT_VALID"

    if not candidate.sensor_id or not reading.sensor_id:
        return None, "SENSOR_REFERENCE_MISSING"

    if candidate.sensor_id == reading.sensor_id:
        return None, "SAME_SENSOR_NOT_INDEPENDENT"

    error, _decision = _validate_sensor_and_run(
        candidate,
        "independent",
    )
    if error:
        return None, f"INDEPENDENT_{error}"

    return candidate, None


def evaluate_reading_trust(reading, cross_check_reading=None):
    """
    Evaluate whether a synthetic reading is suitable for downstream
    software interpretation.

    This engine evaluates data provenance and acquisition reliability.
    It does not diagnose health conditions.

    CROSS_CHECK means an independent reading is available for review.
    It does not mean values agree or that comparison has occurred.
    """

    base_evidence = {
        "sample_id": str(reading.sample_id),
        "data_quality": reading.data_quality,
        "data_source": reading.data_source,
        "is_synthetic": bool(reading.is_synthetic),
        "sensor_id": reading.sensor_id,
        "simulation_run_id": reading.simulation_run_id,
    }

    if not reading.is_synthetic:
        return _result(
            DECISIONS["ABSTAIN"],
            "NON_SYNTHETIC_DATA_NOT_EVALUATED",
            "This prototype's trust policy is restricted to synthetic demonstration data.",
            "Route the reading to an appropriately validated review workflow.",
            evidence=base_evidence,
        )

    if reading.data_quality == VitalSignReading.DataQuality.UNGRADABLE:
        return _result(
            DECISIONS["ABSTAIN"],
            "READING_UNGRADABLE",
            "The reading is ungradable. Numeric values were not interpreted.",
            "Obtain a new measurement and verify acquisition quality.",
            evidence=base_evidence,
        )

    if reading.data_quality == VitalSignReading.DataQuality.SUSPECT:
        return _result(
            DECISIONS["REMEASURE"],
            "READING_MARKED_SUSPECT",
            "The acquisition pipeline marked this reading as suspect.",
            "Repeat the measurement and inspect the sensor signal.",
            evidence=base_evidence,
        )

    if reading.data_quality != VitalSignReading.DataQuality.VALID:
        return _result(
            DECISIONS["ABSTAIN"],
            "UNKNOWN_DATA_QUALITY",
            "The reading has an unsupported data-quality state.",
            "Verify the data-quality classification before interpretation.",
            evidence=base_evidence,
        )

    error, decision = _validate_sensor_and_run(reading, "primary")

    if error:
        explanations = {
            "SENSOR_REFERENCE_MISSING":
                "No linked sensor is available to establish measurement provenance.",
            "NON_SYNTHETIC_SENSOR_NOT_EVALUATED":
                "The linked sensor is not marked as synthetic demonstration hardware.",
            "SENSOR_CREW_MISMATCH":
                "The linked sensor does not belong to the reading's astronaut.",
            "SENSOR_DISCONNECTED":
                "The linked sensor is marked disconnected.",
            "SENSOR_MARKED_DEGRADED":
                "The linked sensor is marked degraded.",
            "UNKNOWN_SENSOR_STATE":
                "The linked sensor has an unsupported operational state.",
            "SIMULATION_RUN_REFERENCE_MISSING":
                "A simulator reading has no linked simulation run.",
            "SIMULATION_SENSOR_LINK_MISMATCH":
                "The simulation run belongs to a different sensor.",
            "NON_SYNTHETIC_SIMULATION_RUN":
                "The linked simulation run is not marked synthetic.",
            "SIMULATED_SENSOR_DISCONNECTION":
                "The reading belongs to a disconnected-sensor simulation.",
            "SIMULATED_SENSOR_FAULT":
                "The reading belongs to a fault-injected simulation run.",
            "UNKNOWN_SIMULATION_FAULT_MODE":
                "The simulation run has an unsupported fault mode.",
            "SIMULATION_RUN_INCOMPLETE":
                "The associated simulation run did not complete normally.",
        }

        actions = {
            DECISIONS["REMEASURE"]:
                "Inspect the sensor and repeat acquisition using a normal signal configuration.",
            DECISIONS["ABSTAIN"]:
                "Verify sensor provenance and operational state before further interpretation.",
        }

        return _result(
            decision,
            error,
            explanations.get(error, "The reading failed a provenance or reliability check."),
            actions[decision],
            evidence=base_evidence,
        )

    run = reading.simulation_run
    if run is not None:
        base_evidence["fault_mode"] = run.fault_mode
        base_evidence["run_status"] = run.status

    analysis = detect_reading_anomalies(reading)

    if not isinstance(analysis, dict):
        return _result(
            DECISIONS["ABSTAIN"],
            "INVALID_ANALYSIS_RESPONSE",
            "The anomaly analysis layer returned an unsupported response.",
            "Verify the analysis service before further interpretation.",
            evidence=base_evidence,
        )

    findings = analysis.get("findings")
    if not isinstance(findings, list):
        return _result(
            DECISIONS["ABSTAIN"],
            "INVALID_ANALYSIS_EVIDENCE",
            "The anomaly analysis response did not contain valid findings.",
            "Verify the analysis evidence before further interpretation.",
            evidence=base_evidence,
        )

    analysis_status = analysis.get("status")
    is_anomalous = analysis.get("is_anomalous")

    base_evidence["anomaly_analysis"] = {
        "status": analysis_status,
        "is_anomalous": is_anomalous,
        "finding_count": len(findings),
        "model_type": analysis.get("model_type"),
    }

    if analysis_status == "INSUFFICIENT_DATA":
        return _result(
            DECISIONS["ABSTAIN"],
            "ANALYSIS_INSUFFICIENT_DATA",
            "The existing analysis layer reported insufficient data.",
            "Verify acquisition quality before further interpretation.",
            evidence=base_evidence,
        )

    if analysis_status not in ("NORMAL", "WARNING", "CRITICAL"):
        return _result(
            DECISIONS["ABSTAIN"],
            "UNKNOWN_ANALYSIS_STATUS",
            "The anomaly analysis layer returned an unknown status.",
            "Verify the analysis service before further interpretation.",
            evidence=base_evidence,
        )

    if not isinstance(is_anomalous, bool):
        return _result(
            DECISIONS["ABSTAIN"],
            "INVALID_ANOMALY_FLAG",
            "The anomaly analysis layer returned an invalid anomaly flag.",
            "Verify the analysis evidence before further interpretation.",
            evidence=base_evidence,
        )

    if (analysis_status == "NORMAL") != (is_anomalous is False):
        return _result(
            DECISIONS["ABSTAIN"],
            "CONTRADICTORY_ANALYSIS_RESULT",
            "The anomaly status and anomaly flag contradict one another.",
            "Verify the analysis result before further interpretation.",
            evidence=base_evidence,
        )

    if is_anomalous:
        candidate, candidate_error = _independent_evidence(
            reading,
            cross_check_reading,
        )

        if candidate is not None:
            candidate_analysis = detect_reading_anomalies(candidate)

            if not isinstance(candidate_analysis, dict):
                candidate_analysis = {}

            candidate_findings = candidate_analysis.get("findings")
            if not isinstance(candidate_findings, list):
                candidate_findings = []

            base_evidence["independent_reading"] = {
                "sample_id": str(candidate.sample_id),
                "sensor_id": candidate.sensor_id,
                "data_quality": candidate.data_quality,
                "analysis_status": candidate_analysis.get("status"),
                "finding_count": len(candidate_findings),
                "comparison_performed": False,
            }

            return _result(
                DECISIONS["CROSS_CHECK"],
                "ANOMALY_WITH_INDEPENDENT_EVIDENCE",
                "Anomaly rules were triggered and a separate sensor reading is available for independent review. Agreement has not been established.",
                "Compare both sensor records and request human review before relying on either result.",
                evidence=base_evidence,
            )

        return _result(
            DECISIONS["REMEASURE"],
            "ANOMALY_REQUIRES_VERIFICATION",
            "The existing demonstration anomaly detector reported one or more findings. This is not a diagnosis.",
            "Repeat the measurement. An independent sensor reading may also be collected for cross-checking.",
            evidence=base_evidence,
            cross_check_unavailable_reason=candidate_error,
        )

    return _result(
        DECISIONS["ACCEPT"],
        "QUALITY_AND_PROVENANCE_CHECKS_PASSED",
        "The reading passed the configured software quality and provenance checks, with no existing demonstration anomaly rule triggered.",
        "Allow downstream software processing with the synthetic-data disclaimer retained.",
        evidence=base_evidence,
    )
