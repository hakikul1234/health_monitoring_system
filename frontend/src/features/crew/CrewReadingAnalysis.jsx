import { useState } from "react";

import {
  Activity,
  AlertCircle,
  BrainCircuit,
  ChevronDown,
  ChevronUp,
  LoaderCircle,
  ShieldCheck,
} from "lucide-react";

import { getHealthReadingAnalysis } from "./crewHealthService";
import PredictiveAnalyticsPanel from "./PredictiveAnalyticsPanel";

import "./CrewReadingAnalysis.css";

function formatLabel(value) {
  return String(value || "UNKNOWN")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatParameter(value) {
  const labels = {
    heart_rate_bpm: "Heart rate",
    spo2_percent: "SpO2",
    body_temperature_c: "Body temperature",
    respiratory_rate_bpm: "Respiratory rate",
  };

  return labels[value] || formatLabel(value);
}

function formatValue(value, parameter) {
  if (value === null || value === undefined) {
    return "--";
  }

  const units = {
    heart_rate_bpm: " BPM",
    spo2_percent: "%",
    body_temperature_c: " °C",
    respiratory_rate_bpm: " /min",
  };

  return `${value}${units[parameter] || ""}`;
}

function StatusBadge({ status }) {
  const normalized = String(status || "UNKNOWN")
    .toLowerCase()
    .replaceAll("_", "-");

  return (
    <span className={`crew-ai-status crew-ai-status-${normalized}`}>
      {formatLabel(status)}
    </span>
  );
}

function AnalysisSection({ title, icon: Icon, children, className = "" }) {
  return (
    <section className={`crew-ai-section ${className}`}>
      <div className="crew-ai-section-heading">
        <div className="crew-ai-section-icon">
          <Icon size={16} />
        </div>
        <h4>{title}</h4>
      </div>

      {children}
    </section>
  );
}


const BASELINE_FEATURES = [
  {
    key: "heart_rate_bpm",
    label: "Heart rate",
    unit: "BPM",
  },
  {
    key: "spo2_percent",
    label: "SpO2",
    unit: "%",
  },
  {
    key: "body_temperature_c",
    label: "Body temperature",
    unit: "°C",
  },
  {
    key: "respiratory_rate_bpm",
    label: "Respiratory rate",
    unit: "/min",
  },
];

function formatMetric(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "--";
  }

  return value.toFixed(4);
}

function PersonalBaselineSection({ baseline }) {
  const features = baseline?.features || {};
  const status = baseline?.status || "UNKNOWN";

  return (
    <AnalysisSection
      title="Astronaut Personal Baseline Intelligence"
      icon={Activity}
      className="crew-ai-baseline-section"
    >
      <div className="crew-ai-baseline-summary">
        <div>
          <span>Baseline status</span>
          <StatusBadge status={status} />
        </div>

        <div>
          <span>Historical samples</span>
          <strong>
            {baseline?.baseline_readings ?? 0}
            {" / "}
            {baseline?.minimum_required ?? 10}
          </strong>
        </div>

        <div>
          <span>Reference window</span>
          <strong>{baseline?.window_days ?? "--"} days</strong>
        </div>

        <div>
          <span>Robust Z threshold</span>
          <strong>
            {typeof baseline?.robust_z_threshold === "number"
              ? baseline.robust_z_threshold
              : "--"}
          </strong>
        </div>
      </div>

      <p className="crew-ai-explanation">
        {baseline?.explanation || "No personal baseline explanation available."}
      </p>

      {status === "INSUFFICIENT_DATA" && (
        <div className="crew-ai-baseline-notice">
          Historical data is insufficient for a personal baseline comparison.
          More eligible VALID synthetic readings are required.
        </div>
      )}

      {status === "NOT_EVALUATED" && (
        <div className="crew-ai-baseline-notice">
          This reading was not evaluated by the personal baseline engine.
        </div>
      )}

      {status === "INVALID_FEATURES" && (
        <div className="crew-ai-baseline-notice">
          One or more telemetry features are missing or invalid. Baseline
          comparison was stopped.
        </div>
      )}

      {status === "INSUFFICIENT_VARIABILITY" && (
        <div className="crew-ai-baseline-notice">
          The historical feature variability is insufficient for reliable
          robust Z-score calculations.
        </div>
      )}

      {Object.keys(features).length > 0 && (
        <div className="crew-ai-baseline-features">
          {BASELINE_FEATURES.map((feature) => {
            const item = features[feature.key];

            if (!item) {
              return null;
            }

            return (
              <article
                className="crew-ai-baseline-feature"
                key={feature.key}
              >
                <div className="crew-ai-baseline-feature-heading">
                  <strong>{feature.label}</strong>
                  <StatusBadge status={item.status} />
                </div>

                <div className="crew-ai-baseline-values">
                  <div>
                    <span>Current</span>
                    <strong>
                      {formatMetric(item.current_value)}
                      {" "}
                      {feature.unit}
                    </strong>
                  </div>

                  <div>
                    <span>Baseline median</span>
                    <strong>
                      {formatMetric(item.baseline_median)}
                      {" "}
                      {feature.unit}
                    </strong>
                  </div>

                  <div>
                    <span>MAD</span>
                    <strong>{formatMetric(item.baseline_mad)}</strong>
                  </div>

                  <div>
                    <span>Robust Z-score</span>
                    <strong>{formatMetric(item.robust_z_score)}</strong>
                  </div>
                </div>

                <div className="crew-ai-baseline-deviation">
                  <span>Deviation detected</span>
                  <StatusBadge
                    status={
                      item.deviation_detected === true
                        ? "DEVIATION"
                        : item.deviation_detected === false
                          ? "WITHIN_BASELINE"
                          : "INSUFFICIENT_DATA"
                    }
                  />
                </div>

                {item.explanation && (
                  <p>{item.explanation}</p>
                )}
              </article>
            );
          })}
        </div>
      )}

      <div className="crew-ai-validation">
        <ShieldCheck size={15} />
        Clinical validation: Not performed
      </div>

      <p className="crew-ai-score-note">
        Robust Z-scores are statistical deviation indicators, not medical risk
        scores or diagnoses. A zero MAD means a reliable score cannot be
        calculated for that feature.
      </p>
    </AnalysisSection>
  );
}

function CrewReadingAnalysis({ readingId }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleToggle = async () => {
    if (isOpen) {
      setIsOpen(false);
      return;
    }

    setIsOpen(true);

    if (result || isLoading) {
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const response = await getHealthReadingAnalysis(readingId);

      if (
        !response?.success ||
        !response?.analysis ||
        !response?.ml_analysis ||
        !response?.personal_baseline ||
        !response?.predictive_analytics
      ) {
        throw new Error("The analysis API returned an incomplete response.");
      }

      setResult(response);
    } catch (requestError) {
      const message =
        requestError.response?.data?.detail ||
        requestError.message ||
        "Unable to retrieve AI analysis.";

      setError(String(message));
    } finally {
      setIsLoading(false);
    }
  };

  const ruleAnalysis = result?.analysis;
  const mlAnalysis = result?.ml_analysis;
  const personalBaseline = result?.personal_baseline;

  return (
    <div className="crew-ai-analysis">
      <button
        type="button"
        className="crew-ai-toggle"
        onClick={handleToggle}
        aria-expanded={isOpen}
      >
        <span className="crew-ai-toggle-label">
          <BrainCircuit size={17} />
          Run AI analysis
        </span>

        {isOpen ? (
          <ChevronUp size={17} />
        ) : (
          <ChevronDown size={17} />
        )}
      </button>

      {isOpen && (
        <div className="crew-ai-content">
          {isLoading && (
            <div className="crew-ai-state">
              <LoaderCircle size={21} className="crew-ai-spin" />
              <strong>Running analysis...</strong>
              <span>Requesting rule-based and ML inference results.</span>
            </div>
          )}

          {error && !isLoading && (
            <div className="crew-ai-error">
              <AlertCircle size={18} />
              <div>
                <strong>Analysis unavailable</strong>
                <p>{error}</p>
              </div>

              <button
                type="button"
                onClick={() => {
                  setResult(null);
                  setError("");
                  setIsOpen(false);
                }}
              >
                Close
              </button>
            </div>
          )}

          {result && !isLoading && (
            <>
              <div className="crew-ai-reading-meta">
                <span>Reading #{result.reading?.id ?? readingId}</span>
                <StatusBadge status={result.reading?.data_quality} />
                <span>
                  {result.reading?.is_synthetic
                    ? "Synthetic reading"
                    : "Non-synthetic reading"}
                </span>
              </div>

              <AnalysisSection
                title="Rule-Based Analysis"
                icon={Activity}
              >
                <div className="crew-ai-result-row">
                  <div>
                    <span>Detection status</span>
                    <StatusBadge status={ruleAnalysis?.status} />
                  </div>

                  <div>
                    <span>Severity</span>
                    <strong>{formatLabel(ruleAnalysis?.severity)}</strong>
                  </div>

                  <div>
                    <span>Findings</span>
                    <strong>{ruleAnalysis?.findings?.length ?? 0}</strong>
                  </div>
                </div>

                <p className="crew-ai-explanation">
                  {ruleAnalysis?.explanation || "No explanation available."}
                </p>

                {ruleAnalysis?.findings?.length > 0 ? (
                  <div className="crew-ai-findings">
                    {ruleAnalysis.findings.map((finding, index) => (
                      <div
                        className="crew-ai-finding"
                        key={`${finding.rule}-${index}`}
                      >
                        <div className="crew-ai-finding-top">
                          <strong>{formatParameter(finding.parameter)}</strong>
                          <StatusBadge status={finding.severity} />
                        </div>

                        <span>
                          Observed: {formatValue(
                            finding.observed_value,
                            finding.parameter
                          )}
                        </span>

                        <span className="crew-ai-rule-code">
                          {finding.rule}
                        </span>

                        <p>{finding.explanation}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="crew-ai-no-findings">
                    No configured demonstration rules were triggered.
                  </div>
                )}
              </AnalysisSection>

              <AnalysisSection
                title="Isolation Forest ML Analysis"
                icon={BrainCircuit}
                className="crew-ai-ml-section"
              >
                <div className="crew-ai-model-meta">
                  <span>{mlAnalysis?.model_type || "ML MODEL"}</span>
                  <span>{mlAnalysis?.model_version || "Version unavailable"}</span>
                </div>

                <div className="crew-ai-result-row">
                  <div>
                    <span>Prediction status</span>
                    <StatusBadge status={mlAnalysis?.status} />
                  </div>

                  <div>
                    <span>Anomaly score</span>
                    <strong>
                      {typeof mlAnalysis?.anomaly_score === "number"
                        ? mlAnalysis.anomaly_score.toFixed(4)
                        : "--"}
                    </strong>
                  </div>

                  <div>
                    <span>Decision threshold</span>
                    <strong>
                      {typeof mlAnalysis?.threshold === "number"
                        ? mlAnalysis.threshold.toFixed(4)
                        : "--"}
                    </strong>
                  </div>
                </div>

                <p className="crew-ai-explanation">
                  {mlAnalysis?.explanation || "No ML explanation available."}
                </p>

                {mlAnalysis?.score_interpretation && (
                  <p className="crew-ai-score-note">
                    {mlAnalysis.score_interpretation}
                  </p>
                )}

                <div className="crew-ai-validation">
                  <ShieldCheck size={15} />
                  Clinical validation:{" "}
                  {mlAnalysis?.clinical_validation === false
                    ? "Not performed"
                    : "Not confirmed"}
                </div>

                {mlAnalysis?.error_type && (
                  <p className="crew-ai-score-note">
                    Technical error: {mlAnalysis.error_type}
                  </p>
                )}
              </AnalysisSection>

              <PersonalBaselineSection baseline={personalBaseline} />

              <PredictiveAnalyticsPanel
                predictive={result.predictive_analytics}
              />

              <div className="crew-ai-disclaimer">
                <AlertCircle size={16} />
                <p>
                  {result.disclaimer ||
                    "Synthetic software demonstration only. Not a medical diagnosis or treatment recommendation. Human review is required."}
                </p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default CrewReadingAnalysis;
