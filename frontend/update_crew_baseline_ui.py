from pathlib import Path

jsx_path = Path("src/features/crew/CrewReadingAnalysis.jsx")
css_path = Path("src/features/crew/CrewReadingAnalysis.css")

jsx = jsx_path.read_text(encoding="utf-8-sig")

anchor = "function CrewReadingAnalysis({ readingId }) {"

baseline_component = r'''
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

'''

if "function PersonalBaselineSection({ baseline })" not in jsx:
    if anchor not in jsx:
        raise SystemExit("Could not locate CrewReadingAnalysis component anchor.")
    jsx = jsx.replace(anchor, baseline_component + anchor, 1)

old_validation = """if (!response?.success || !response?.analysis || !response?.ml_analysis) {
        throw new Error("The analysis API returned an incomplete response.");
      }"""

new_validation = """if (
        !response?.success ||
        !response?.analysis ||
        !response?.ml_analysis ||
        !response?.personal_baseline
      ) {
        throw new Error("The analysis API returned an incomplete response.");
      }"""

if old_validation in jsx:
    jsx = jsx.replace(old_validation, new_validation, 1)
elif new_validation not in jsx:
    raise SystemExit("Could not locate analysis response validation.")

old_vars = """  const ruleAnalysis = result?.analysis;
  const mlAnalysis = result?.ml_analysis;"""

new_vars = """  const ruleAnalysis = result?.analysis;
  const mlAnalysis = result?.ml_analysis;
  const personalBaseline = result?.personal_baseline;"""

if old_vars in jsx:
    jsx = jsx.replace(old_vars, new_vars, 1)
elif new_vars not in jsx:
    raise SystemExit("Could not locate analysis state variables.")

render_anchor = """              <div className="crew-ai-disclaimer">"""

baseline_render = """              <PersonalBaselineSection baseline={personalBaseline} />

              <div className="crew-ai-disclaimer">"""

if render_anchor in jsx:
    jsx = jsx.replace(render_anchor, baseline_render, 1)
elif baseline_render not in jsx:
    raise SystemExit("Could not locate disclaimer render anchor.")

jsx_path.write_text(jsx, encoding="utf-8")

css_addition = r"""

/* Personal baseline intelligence */

.crew-ai-baseline-section {
  border-color: rgba(56, 189, 248, 0.28);
  background: rgba(14, 116, 144, 0.045);
}

.crew-ai-baseline-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 9px;
}

.crew-ai-baseline-summary > div {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 7px;
  min-width: 0;
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: rgba(17, 29, 53, 0.65);
}

.crew-ai-baseline-summary > div > span,
.crew-ai-baseline-values span,
.crew-ai-baseline-deviation > span {
  color: var(--color-text-muted);
  font-size: 9px;
}

.crew-ai-baseline-summary strong {
  color: var(--color-text);
  font-size: 11px;
}

.crew-ai-baseline-features {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
  margin-top: 13px;
}

.crew-ai-baseline-feature {
  min-width: 0;
  padding: 11px;
  border: 1px solid var(--color-border);
  border-radius: 9px;
  background: rgba(17, 29, 53, 0.55);
}

.crew-ai-baseline-feature-heading,
.crew-ai-baseline-deviation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.crew-ai-baseline-feature-heading strong {
  color: var(--color-text);
  font-size: 10px;
}

.crew-ai-baseline-values {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 11px;
  margin-top: 13px;
}

.crew-ai-baseline-values > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.crew-ai-baseline-values strong {
  color: var(--color-text);
  font-size: 10px;
  overflow-wrap: anywhere;
}

.crew-ai-baseline-deviation {
  margin-top: 12px;
  padding-top: 9px;
  border-top: 1px solid var(--color-border);
}

.crew-ai-baseline-feature > p {
  margin-top: 9px;
  color: var(--color-text-muted);
  font-size: 9px;
  line-height: 1.5;
}

.crew-ai-baseline-notice {
  margin-top: 12px;
  padding: 11px;
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-radius: 8px;
  background: rgba(245, 158, 11, 0.05);
  color: var(--color-text-secondary);
  font-size: 10px;
  line-height: 1.6;
}

.crew-ai-status-deviation {
  color: var(--color-danger);
  background: rgba(239, 68, 68, 0.08);
}

.crew-ai-status-within-baseline {
  color: var(--color-success);
  background: rgba(34, 197, 94, 0.08);
}

.crew-ai-status-zero-mad,
.crew-ai-status-insufficient-variability,
.crew-ai-status-invalid-reading {
  color: var(--color-warning);
  background: rgba(245, 158, 11, 0.08);
}

@media (max-width: 600px) {
  .crew-ai-baseline-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .crew-ai-baseline-features {
    grid-template-columns: 1fr;
  }
}
"""

css = css_path.read_text(encoding="utf-8-sig")

if "/* Personal baseline intelligence */" not in css:
    css_path.write_text(css.rstrip() + "\n" + css_addition, encoding="utf-8")

print("CREW HEALTH PERSONAL BASELINE UI UPDATED")
print("Existing rule-based and ML sections preserved")
print("Baseline feature metrics added")
print("Responsive baseline styles added")
