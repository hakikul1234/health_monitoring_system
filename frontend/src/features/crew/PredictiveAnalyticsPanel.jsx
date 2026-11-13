import {
  Activity,
  AlertCircle,
  Clock,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  Minus,
} from "lucide-react";

import "./PredictiveAnalyticsPanel.css";

const FEATURES = [
  {
    key: "heart_rate_bpm",
    label: "Heart rate",
    unit: "BPM",
  },
  {
    key: "spo2_percent",
    label: "SpO₂",
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

function formatLabel(value) {
  return String(value || "UNKNOWN")
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatNumber(value, decimals = 3) {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "--";
  }

  return value.toFixed(decimals);
}

function formatDuration(seconds) {
  if (typeof seconds !== "number" || !Number.isFinite(seconds)) {
    return "--";
  }

  if (seconds >= 60) {
    return `${(seconds / 60).toFixed(1)} minutes`;
  }

  return `${seconds.toFixed(0)} seconds`;
}

function DirectionIcon({ direction }) {
  if (direction === "INCREASING") {
    return <TrendingUp size={14} />;
  }

  if (direction === "DECREASING") {
    return <TrendingDown size={14} />;
  }

  return <Minus size={14} />;
}

function PredictiveAnalyticsPanel({ predictive }) {
  const status = predictive?.status || "NOT_EVALUATED";
  const isEstimated = status === "TREND_ESTIMATED";
  const features = predictive?.features || {};

  return (
    <section className="predictive-panel">
      <div className="predictive-heading">
        <div className="predictive-title">
          <Activity size={17} />
          <strong>Predictive Health Trend</strong>
        </div>

        <span className={`predictive-status predictive-status-${status.toLowerCase().replaceAll("_", "-")}`}>
          {formatLabel(status)}
        </span>
      </div>

      <div className="predictive-summary">
        <div>
          <span>Algorithm</span>
          <strong>{predictive?.algorithm || "Unavailable"}</strong>
        </div>

        <div>
          <span>Model version</span>
          <strong>{predictive?.model_version || "--"}</strong>
        </div>

        <div>
          <span>Historical readings</span>
          <strong>
            {predictive?.historical_readings ?? 0}
            {" / "}
            {predictive?.minimum_required ?? 10}
          </strong>
        </div>

        <div>
          <span>History span</span>
          <strong>
            {formatDuration(predictive?.history_span_seconds)}
          </strong>
        </div>

        <div>
          <span>Forecast horizon</span>
          <strong>
            {formatDuration(predictive?.forecast_horizon_seconds)}
          </strong>
        </div>
      </div>

      {!isEstimated && (
        <div className="predictive-notice">
          <AlertCircle size={16} />
          <div>
            <strong>
              {status === "INSUFFICIENT_DATA"
                ? "Insufficient historical data"
                : status === "INVALID_FEATURES"
                  ? "Invalid telemetry features"
                  : status === "NOT_EVALUATED"
                    ? "Trend estimation not performed"
                    : "Prediction unavailable"}
            </strong>

            <p>
              {predictive?.explanation ||
                "A trend estimate is not available for this reading. No predicted values are displayed."}
            </p>

            <p>
              Trend estimation requires at least{" "}
              {predictive?.minimum_required ?? 10} eligible historical
              readings spanning at least 300 seconds.
            </p>
          </div>
        </div>
      )}

      {isEstimated && (
        <>
          <div className="predictive-feature-grid">
            {FEATURES.map((feature) => {
              const item = features[feature.key];

              if (!item) {
                return null;
              }

              const direction = item.trend_direction || "STABLE";

              return (
                <article
                  className="predictive-feature"
                  key={feature.key}
                >
                  <div className="predictive-feature-heading">
                    <strong>{feature.label}</strong>

                    <span className={`predictive-direction predictive-direction-${direction.toLowerCase()}`}>
                      <DirectionIcon direction={direction} />
                      {formatLabel(direction)}
                    </span>
                  </div>

                  <div className="predictive-values">
                    <div>
                      <span>Latest</span>
                      <strong>
                        {formatNumber(item.latest)}
                        {" "}
                        {feature.unit}
                      </strong>
                    </div>

                    <div>
                      <span>Estimated value</span>
                      <strong>
                        {formatNumber(item.predicted_value)}
                        {" "}
                        {feature.unit}
                      </strong>
                    </div>

                    <div>
                      <span>Slope / minute</span>
                      <strong>
                        {formatNumber(item.slope_per_minute)}
                      </strong>
                    </div>

                    <div>
                      <span>Regression RMSE</span>
                      <strong>
                        {formatNumber(item.regression_rmse)}
                      </strong>
                    </div>

                    <div>
                      <span>Observed change</span>
                      <strong>
                        {formatNumber(item.observed_change)}
                      </strong>
                    </div>
                  </div>

                  {item.explanation && (
                    <p className="predictive-explanation">
                      {item.explanation}
                    </p>
                  )}
                </article>
              );
            })}
          </div>

          {Object.keys(features).length === 0 && (
            <div className="predictive-notice">
              Feature-level trend information is unavailable.
            </div>
          )}
        </>
      )}

      <div className="predictive-disclaimer">
        <ShieldCheck size={15} />
        <span>
          Research-only statistical extrapolation. Clinical validation:{" "}
          {predictive?.clinical_validation === false
            ? "Not performed"
            : "Not confirmed"}
          . Synthetic demonstration data only; not a medical forecast,
          diagnosis, or risk score. Human review is required.
        </span>
      </div>

      <div className="predictive-method-note">
        <Clock size={13} />
        Forecast horizon: 5 minutes. Estimates depend on eligible historical
        synthetic readings and do not establish physiological predictive validity.
      </div>
    </section>
  );
}

export default PredictiveAnalyticsPanel;
