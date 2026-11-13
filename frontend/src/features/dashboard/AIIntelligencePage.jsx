import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  BrainCircuit,
  CheckCircle2,
  CircleAlert,
  Clock,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

import {
  getHealthReadings,
  getHealthReadingAnalysis,
} from "../crew/crewHealthService";

import PredictiveAnalyticsPanel from "../crew/PredictiveAnalyticsPanel";

import "./AIIntelligencePage.css";

function formatLabel(value) {
  return String(value || "UNKNOWN")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value) {
  if (!value) return "Time unavailable";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "Time unavailable";

  return date.toLocaleString();
}

function StatusBadge({ status }) {
  const normalized = String(status || "UNKNOWN")
    .toLowerCase()
    .replaceAll("_", "-");

  return (
    <span className={`ai-page-status ai-page-status-${normalized}`}>
      {formatLabel(status)}
    </span>
  );
}

function MetricCard({ icon: Icon, label, value, detail, color }) {
  return (
    <article className={`ai-page-metric ai-page-metric-${color}`}>
      <div className="ai-page-metric-top">
        <span>{label}</span>
        <div className="ai-page-metric-icon">
          <Icon size={19} />
        </div>
      </div>

      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
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

function RuleAnalysisPanel({ analysis }) {
  const findings = Array.isArray(analysis?.findings)
    ? analysis.findings
    : [];

  return (
    <div className="ai-page-result ai-page-rule-result">
      <div className="ai-page-result-heading">
        <strong>Rule-Based Analysis</strong>
        <StatusBadge status={analysis?.status} />
      </div>

      <div className="ai-page-result-values">
        <div>
          <span>Detection status</span>
          <strong>{formatLabel(analysis?.status)}</strong>
        </div>

        <div>
          <span>Severity</span>
          <strong>{formatLabel(analysis?.severity)}</strong>
        </div>

        <div>
          <span>Rule findings</span>
          <strong>{findings.length}</strong>
        </div>
      </div>

      <p>
        {analysis?.explanation || "No rule-based explanation available."}
      </p>
    </div>
  );
}

function PersonalBaselinePanel({ baseline }) {
  const features = baseline?.features || {};
  const status = baseline?.status || "UNKNOWN";

  return (
    <div className="ai-page-result ai-page-baseline-result">
      <div className="ai-page-result-heading">
        <strong>
          <Activity size={15} />
          Personal Baseline Intelligence
        </strong>
        <StatusBadge status={status} />
      </div>

      <div className="ai-page-result-values ai-page-baseline-summary">
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
          <strong>
            {baseline?.window_days ?? "--"} days
          </strong>
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

      <p>
        {baseline?.explanation || "No personal baseline explanation available."}
      </p>

      {status === "INSUFFICIENT_DATA" && (
        <div className="ai-page-baseline-notice">
          Insufficient eligible historical readings. At least
          {" "}
          {baseline?.minimum_required ?? 10}
          {" "}
          VALID synthetic readings are required.
        </div>
      )}

      {status === "NOT_EVALUATED" && (
        <div className="ai-page-baseline-notice">
          Personal baseline analysis was not performed for this reading.
        </div>
      )}

      {status === "INVALID_FEATURES" && (
        <div className="ai-page-baseline-notice">
          Missing or invalid telemetry features prevented baseline analysis.
        </div>
      )}

      {status === "INSUFFICIENT_VARIABILITY" && (
        <div className="ai-page-baseline-notice">
          Historical variability was insufficient for reliable robust
          Z-score calculations.
        </div>
      )}

      {Object.keys(features).length > 0 && (
        <div className="ai-page-baseline-grid">
          {BASELINE_FEATURES.map((feature) => {
            const item = features[feature.key];

            if (!item) return null;

            return (
              <article
                className="ai-page-baseline-feature"
                key={feature.key}
              >
                <div className="ai-page-baseline-feature-heading">
                  <strong>{feature.label}</strong>
                  <StatusBadge status={item.status} />
                </div>

                <div className="ai-page-baseline-metrics">
                  <div>
                    <span>Current value</span>
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

                <div className="ai-page-baseline-deviation">
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

      {Object.keys(features).length === 0 && (
        <div className="ai-page-baseline-notice">
          Feature-level baseline metrics are unavailable for this reading.
          No missing values have been inferred.
        </div>
      )}

      <div className="ai-page-baseline-disclaimer">
        <ShieldCheck size={14} />
        Research-only statistical comparison · Clinical validation not performed
      </div>
    </div>
  );
}

function AIIntelligencePage() {
  const [readings, setReadings] = useState([]);
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(true);
  const [loadingId, setLoadingId] = useState(null);
  const [error, setError] = useState("");
  const [analysisErrors, setAnalysisErrors] = useState({});

  const loadReadings = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await getHealthReadings();

      const recentSynthetic = data
        .filter((reading) => reading.is_synthetic === true)
        .sort(
          (a, b) =>
            new Date(b.recorded_at).getTime() -
            new Date(a.recorded_at).getTime()
        )
        .slice(0, 12);

      setReadings(recentSynthetic);
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
        requestError.message ||
        "Unable to load synthetic health readings."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReadings();
  }, [loadReadings]);

  const runAnalysis = async (readingId) => {
    setLoadingId(readingId);

    setAnalysisErrors((previous) => ({
      ...previous,
      [readingId]: "",
    }));

    try {
      const response = await getHealthReadingAnalysis(readingId);

      if (
        !response?.success ||
        !response?.analysis ||
        !response?.ml_analysis ||
        !response?.personal_baseline ||
        !response?.predictive_analytics
      ) {
        throw new Error("Incomplete AI analysis response.");
      }

      setResults((previous) => ({
        ...previous,
        [readingId]: response,
      }));
    } catch (requestError) {
      setAnalysisErrors((previous) => ({
        ...previous,
        [readingId]:
          requestError.response?.data?.detail ||
          requestError.message ||
          "Analysis request failed.",
      }));
    } finally {
      setLoadingId(null);
    }
  };

  const statistics = useMemo(() => {
    const analyses = Object.values(results);
    const mlResults = analyses.map((item) => item.ml_analysis);

    return {
      evaluated: mlResults.filter(
        (item) =>
          item.status === "NORMAL" || item.status === "ANOMALY"
      ).length,

      normal: mlResults.filter(
        (item) => item.status === "NORMAL"
      ).length,

      anomalies: mlResults.filter(
        (item) => item.status === "ANOMALY"
      ).length,

      insufficient: mlResults.filter(
        (item) => item.status === "INSUFFICIENT_DATA"
      ).length,

      skipped: mlResults.filter(
        (item) =>
          !["NORMAL", "ANOMALY", "INSUFFICIENT_DATA"].includes(item.status)
      ).length,
    };
  }, [results]);

  return (
    <div className="page-container ai-intelligence-page">
      <section className="ai-page-heading">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-line" />
            ASTRA-PULSE MACHINE LEARNING
          </div>

          <h1>
            AI <span className="gradient-text">Intelligence</span>
          </h1>

          <p>
            Explore synthetic crew telemetry using the Isolation Forest
            anomaly detection engine.
          </p>
        </div>

        <button
          className="ai-page-refresh"
          type="button"
          onClick={() => {
            setResults({});
            setAnalysisErrors({});
            loadReadings();
          }}
          disabled={loading}
        >
          <RefreshCw size={16} />
          Refresh readings
        </button>
      </section>

      <div className="ai-page-notice">
        <ShieldCheck size={19} />
        <div>
          <strong>Research prototype · Synthetic data only</strong>
          <p>
            Model outputs are experimental software results, not medical
            diagnoses or treatment recommendations. Human review is required.
          </p>
        </div>
      </div>

      <section className="ai-page-model-card">
        <div className="ai-page-model-icon">
          <BrainCircuit size={27} />
        </div>

        <div className="ai-page-model-info">
          <span className="ai-page-overline">ACTIVE MODEL ARTIFACT</span>
          <h2>Isolation Forest</h2>
          <p>
            Unsupervised anomaly detection · Four synthetic vital-sign features
          </p>
        </div>

        <div className="ai-page-model-version">
          <span>MODEL VERSION</span>
          <strong>v1.0.0</strong>
          <StatusBadge status="enabled" />
        </div>
      </section>

      <section className="ai-page-metrics">
        <MetricCard
          icon={Activity}
          label="Evaluated"
          value={statistics.evaluated}
          detail="Current page session"
          color="blue"
        />

        <MetricCard
          icon={CheckCircle2}
          label="Normal"
          value={statistics.normal}
          detail="ML normal predictions"
          color="green"
        />

        <MetricCard
          icon={CircleAlert}
          label="Anomalies"
          value={statistics.anomalies}
          detail="ML anomaly predictions"
          color="red"
        />

        <MetricCard
          icon={ShieldCheck}
          label="Insufficient data"
          value={statistics.insufficient}
          detail="Interpretation blocked"
          color="orange"
        />
      </section>

      <section className="ai-page-benchmark">
        <div className="ai-page-section-heading">
          <div>
            <span className="ai-page-overline">OFFLINE EVALUATION</span>
            <h2>Synthetic Benchmark</h2>
          </div>
          <span className="ai-page-benchmark-label">
            <Target size={14} />
            Test dataset
          </span>
        </div>

        <div className="ai-page-benchmark-grid">
          <div>
            <span>Accuracy</span>
            <strong>98.33%</strong>
          </div>
          <div>
            <span>Precision</span>
            <strong>97.56%</strong>
          </div>
          <div>
            <span>Recall</span>
            <strong>100%</strong>
          </div>
          <div>
            <span>F1 Score</span>
            <strong>98.77%</strong>
          </div>
          <div>
            <span>ROC-AUC</span>
            <strong>1.000</strong>
          </div>
          <div>
            <span>PR-AUC</span>
            <strong>1.000</strong>
          </div>
        </div>

        <p className="ai-page-benchmark-note">
          <TrendingUp size={15} />
          Offline benchmark: 1,500 synthetic test samples, with a 5% target
          false-positive rate. These results do not establish real-world,
          clinical, or astronaut-health accuracy.
        </p>
      </section>

      <section className="ai-page-readings">
        <div className="ai-page-section-heading">
          <div>
            <span className="ai-page-overline">LIVE API DATA</span>
            <h2>Recent Synthetic Readings</h2>
          </div>

          <span className="ai-page-reading-count">
            {readings.length} readings loaded
          </span>
        </div>

        {loading && (
          <div className="ai-page-state">
            <RefreshCw size={21} className="ai-page-spin" />
            <strong>Loading telemetry readings...</strong>
          </div>
        )}

        {error && !loading && (
          <div className="ai-page-error">
            <AlertCircle size={19} />
            <span>{error}</span>
            <button type="button" onClick={loadReadings}>
              Retry
            </button>
          </div>
        )}

        {!loading && !error && readings.length === 0 && (
          <div className="ai-page-state">
            <Activity size={23} />
            <strong>No synthetic readings available</strong>
            <span>Generate telemetry using the Simulator module.</span>
          </div>
        )}

        <div className="ai-page-reading-list">
          {readings.map((reading) => {
            const result = results[reading.id];
            const ml = result?.ml_analysis;
            const analysisError = analysisErrors[reading.id];

            return (
              <article
                className="ai-page-reading-card"
                key={reading.id}
              >
                <div className="ai-page-reading-top">
                  <div>
                    <strong>
                      Reading #{reading.id}
                    </strong>
                    <span>
                      {reading.astronaut_code || "Astronaut unavailable"}
                    </span>
                  </div>

                  <StatusBadge status={reading.data_quality} />
                </div>

                <div className="ai-page-vitals">
                  <div>
                    <span>Heart rate</span>
                    <strong>{reading.heart_rate_bpm ?? "--"} BPM</strong>
                  </div>
                  <div>
                    <span>SpO₂</span>
                    <strong>{reading.spo2_percent ?? "--"}%</strong>
                  </div>
                  <div>
                    <span>Temperature</span>
                    <strong>
                      {reading.body_temperature_c ?? "--"} °C
                    </strong>
                  </div>
                  <div>
                    <span>Respiratory rate</span>
                    <strong>
                      {reading.respiratory_rate_bpm ?? "--"} /min
                    </strong>
                  </div>
                </div>

                <div className="ai-page-reading-bottom">
                  <span>
                    <Clock size={13} />
                    {formatDate(reading.recorded_at)}
                  </span>

                  <button
                    type="button"
                    onClick={() => runAnalysis(reading.id)}
                    disabled={loadingId !== null}
                  >
                    {loadingId === reading.id ? (
                      <>
                        <RefreshCw size={14} className="ai-page-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <BrainCircuit size={15} />
                        {result ? "Run again" : "Run analysis"}
                      </>
                    )}
                  </button>
                </div>

                {analysisError && (
                  <div className="ai-page-inline-error">
                    <AlertCircle size={15} />
                    {analysisError}
                  </div>
                )}

                {result && (
                  <>
                    <RuleAnalysisPanel analysis={result.analysis} />

                    <div className="ai-page-result">
                    <div className="ai-page-result-heading">
                      <strong>ML inference result</strong>
                      <StatusBadge status={ml?.status} />
                    </div>

                    <div className="ai-page-result-values">
                      <div>
                        <span>Anomaly score</span>
                        <strong>
                          {typeof ml?.anomaly_score === "number"
                            ? ml.anomaly_score.toFixed(4)
                            : "--"}
                        </strong>
                      </div>

                      <div>
                        <span>Threshold</span>
                        <strong>
                          {typeof ml?.threshold === "number"
                            ? ml.threshold.toFixed(4)
                            : "--"}
                        </strong>
                      </div>

                      <div>
                        <span>Rule findings</span>
                        <strong>
                          {result.analysis?.findings?.length ?? 0}
                        </strong>
                      </div>
                    </div>

                    <p>{ml?.explanation || "No explanation available."}</p>
                    <small>
                      {ml?.score_interpretation || ""}
                    </small>
                  </div>

                    <PersonalBaselinePanel
                      baseline={result.personal_baseline}
                    />

                    <PredictiveAnalyticsPanel
                      predictive={result.predictive_analytics}
                    />
                  </>
                )}
              </article>
            );
          })}
        </div>
      </section>

      <footer className="ai-page-footer">
        <Sparkles size={15} />
        ASTRA-PULSE AI 2.0 · Experimental software research prototype
      </footer>
    </div>
  );
}

export default AIIntelligencePage;
