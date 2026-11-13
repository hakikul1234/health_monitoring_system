from dataclasses import dataclass, asdict


# ----------------------------------------------------------
# DEMONSTRATION RULE THRESHOLDS
# NOT CLINICAL OR DIAGNOSTIC LIMITS
# ----------------------------------------------------------

RULE_THRESHOLDS = {
    "heart_rate_bpm": {
        "warning_low": 50,
        "warning_high": 110,
        "critical_high": 150,
    },

    "spo2_percent": {
        "warning_low": 95,
        "critical_low": 88,
    },

    "body_temperature_c": {
        "warning_high": 38.0,
        "critical_high": 39.0,
    },

    "respiratory_rate_bpm": {
        "warning_low": 10,
        "warning_high": 24,
        "critical_high": 30,
    },
}


@dataclass
class AnomalyFinding:

    parameter: str
    observed_value: float
    severity: str
    rule: str
    explanation: str

    def to_dict(self):
        return asdict(self)


def detect_reading_anomalies(reading):
    """
    Analyze one synthetic health reading.

    Returns an explainable, rule-based demonstration result.

    This service is not a medical diagnostic system.
    """

    quality = str(reading.data_quality)

    # ------------------------------------------------------
    # 1. DATA QUALITY GATE
    # ------------------------------------------------------

    if quality.endswith("UNGRADABLE"):

        return {
            "status": "INSUFFICIENT_DATA",
            "severity": "UNKNOWN",
            "is_anomalous": False,
            "findings": [],
            "data_quality": quality,
            "explanation": (
                "Reading is ungradable. "
                "Values must not be interpreted."
            ),
            "synthetic": bool(reading.is_synthetic),
            "model_type": "RULE_BASED_DEMONSTRATION",
            "medical_disclaimer": (
                "Software demonstration only. "
                "Not a medical diagnosis."
            ),
        }

    # ------------------------------------------------------
    # 2. READ VITAL SIGN VALUES
    # ------------------------------------------------------

    values = {
        "heart_rate_bpm": float(reading.heart_rate_bpm),
        "spo2_percent": float(reading.spo2_percent),
        "body_temperature_c": float(
            reading.body_temperature_c
        ),
        "respiratory_rate_bpm": float(
            reading.respiratory_rate_bpm
        ),
    }

    findings = []

    # ------------------------------------------------------
    # 3. HEART RATE RULES
    # ------------------------------------------------------

    hr = values["heart_rate_bpm"]
    hr_rules = RULE_THRESHOLDS["heart_rate_bpm"]

    if hr >= hr_rules["critical_high"]:

        findings.append(
            AnomalyFinding(
                parameter="heart_rate_bpm",
                observed_value=hr,
                severity="CRITICAL",
                rule="HEART_RATE_CRITICAL_HIGH",
                explanation=(
                    "Heart rate reached or exceeded "
                    "the demonstration critical threshold."
                ),
            )
        )

    elif (
        hr < hr_rules["warning_low"]
        or hr > hr_rules["warning_high"]
    ):

        findings.append(
            AnomalyFinding(
                parameter="heart_rate_bpm",
                observed_value=hr,
                severity="WARNING",
                rule="HEART_RATE_OUTSIDE_DEMO_RANGE",
                explanation=(
                    "Heart rate is outside the configured "
                    "demonstration range."
                ),
            )
        )

    # ------------------------------------------------------
    # 4. SPO2 RULES
    # ------------------------------------------------------

    spo2 = values["spo2_percent"]
    spo2_rules = RULE_THRESHOLDS["spo2_percent"]

    if spo2 < spo2_rules["critical_low"]:

        findings.append(
            AnomalyFinding(
                parameter="spo2_percent",
                observed_value=spo2,
                severity="CRITICAL",
                rule="SPO2_CRITICAL_LOW",
                explanation=(
                    "SpO2 reached the demonstration "
                    "critical low threshold."
                ),
            )
        )

    elif spo2 < spo2_rules["warning_low"]:

        findings.append(
            AnomalyFinding(
                parameter="spo2_percent",
                observed_value=spo2,
                severity="WARNING",
                rule="SPO2_BELOW_DEMO_RANGE",
                explanation=(
                    "SpO2 is below the configured "
                    "demonstration range."
                ),
            )
        )

    # ------------------------------------------------------
    # 5. BODY TEMPERATURE RULES
    # ------------------------------------------------------

    temperature = values["body_temperature_c"]
    temp_rules = RULE_THRESHOLDS["body_temperature_c"]

    if temperature >= temp_rules["critical_high"]:

        findings.append(
            AnomalyFinding(
                parameter="body_temperature_c",
                observed_value=temperature,
                severity="CRITICAL",
                rule="TEMPERATURE_CRITICAL_HIGH",
                explanation=(
                    "Temperature reached the demonstration "
                    "critical threshold."
                ),
            )
        )

    elif temperature >= temp_rules["warning_high"]:

        findings.append(
            AnomalyFinding(
                parameter="body_temperature_c",
                observed_value=temperature,
                severity="WARNING",
                rule="TEMPERATURE_ABOVE_DEMO_RANGE",
                explanation=(
                    "Temperature is above the configured "
                    "demonstration range."
                ),
            )
        )

    # ------------------------------------------------------
    # 6. RESPIRATORY RATE RULES
    # ------------------------------------------------------

    respiratory = values["respiratory_rate_bpm"]
    respiratory_rules = RULE_THRESHOLDS[
        "respiratory_rate_bpm"
    ]

    if respiratory >= respiratory_rules["critical_high"]:

        findings.append(
            AnomalyFinding(
                parameter="respiratory_rate_bpm",
                observed_value=respiratory,
                severity="CRITICAL",
                rule="RESPIRATORY_RATE_CRITICAL_HIGH",
                explanation=(
                    "Respiratory rate reached the "
                    "demonstration critical threshold."
                ),
            )
        )

    elif (
        respiratory < respiratory_rules["warning_low"]
        or respiratory > respiratory_rules["warning_high"]
    ):

        findings.append(
            AnomalyFinding(
                parameter="respiratory_rate_bpm",
                observed_value=respiratory,
                severity="WARNING",
                rule="RESPIRATORY_RATE_OUTSIDE_DEMO_RANGE",
                explanation=(
                    "Respiratory rate is outside the "
                    "configured demonstration range."
                ),
            )
        )

    # ------------------------------------------------------
    # 7. OVERALL SEVERITY
    # ------------------------------------------------------

    if any(
        finding.severity == "CRITICAL"
        for finding in findings
    ):

        severity = "CRITICAL"

    elif findings:

        severity = "WARNING"

    else:

        severity = "NORMAL"

    # ------------------------------------------------------
    # 8. BUILD EXPLAINABLE RESULT
    # ------------------------------------------------------

    return {
        "status": severity,
        "severity": severity,
        "is_anomalous": bool(findings),

        "findings": [
            finding.to_dict()
            for finding in findings
        ],

        "data_quality": quality,

        "explanation": (
            "No configured demonstration rules triggered."
            if not findings
            else (
                f"{len(findings)} demonstration "
                "anomaly rule(s) triggered."
            )
        ),

        "synthetic": bool(reading.is_synthetic),

        "model_type": "RULE_BASED_DEMONSTRATION",

        "medical_disclaimer": (
            "Software demonstration only. "
            "Not a medical diagnosis or treatment recommendation."
        ),
    }
