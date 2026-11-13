from pathlib import Path

jsx_path = Path("src/features/dashboard/AIIntelligencePage.jsx")
css_path = Path("src/features/dashboard/AIIntelligencePage.css")

jsx = jsx_path.read_text(encoding="utf-8-sig")

# --------------------------------------------------
# 1. Add Personal Baseline and Rule Analysis panels.
# --------------------------------------------------

component_anchor = "function AIIntelligencePage() {"

components = r'''
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

'''

if "function PersonalBaselinePanel({ baseline })" not in jsx:
    if component_anchor not in jsx:
        raise SystemExit("AIIntelligencePage component anchor not found.")
    jsx = jsx.replace(component_anchor, components + component_anchor, 1)

# --------------------------------------------------
# 2. Require personal_baseline in API response.
# --------------------------------------------------

old_validation = """        !response?.analysis ||
        !response?.ml_analysis
      ) {"""

new_validation = """        !response?.analysis ||
        !response?.ml_analysis ||
        !response?.personal_baseline
      ) {"""

if old_validation in jsx:
    jsx = jsx.replace(old_validation, new_validation, 1)
elif new_validation not in jsx:
    raise SystemExit("Could not locate AI analysis response validation.")

# --------------------------------------------------
# 3. Add Rule-Based and Personal Baseline panels.
# --------------------------------------------------

old_render_start = """                {result && (
                  <div className="ai-page-result">"""

new_render_start = """                {result && (
                  <>
                    <RuleAnalysisPanel analysis={result.analysis} />

                    <div className="ai-page-result">"""

if old_render_start in jsx:
    jsx = jsx.replace(old_render_start, new_render_start, 1)
elif new_render_start not in jsx:
    raise SystemExit("Could not locate result rendering start.")

old_render_end = """                    <small>
                      {ml?.score_interpretation || ""}
                    </small>
                  </div>
                )}"""

new_render_end = """                    <small>
                      {ml?.score_interpretation || ""}
                    </small>
                  </div>

                    <PersonalBaselinePanel
                      baseline={result.personal_baseline}
                    />
                  </>
                )}"""

if old_render_end in jsx:
    jsx = jsx.replace(old_render_end, new_render_end, 1)
elif new_render_end not in jsx:
    raise SystemExit("Could not locate ML result rendering end.")

jsx_path.write_text(jsx, encoding="utf-8")

# --------------------------------------------------
# 4. Add styles without replacing existing CSS.
# --------------------------------------------------

css_addition = r"""

/* Three-layer AI intelligence results */

.ai-page-rule-result {
  border-color: rgba(56, 189, 248, 0.25);
}

.ai-page-baseline-result {
  border-color: rgba(124, 58, 237, 0.28);
  background: rgba(124, 58, 237, 0.045);
}

.ai-page-result-heading > strong {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.ai-page-baseline-summary {
  margin-bottom: 13px;
}

.ai-page-baseline-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 14px;
}

.ai-page-baseline-feature {
  min-width: 0;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 9px;
  background: rgba(17, 29, 53, 0.55);
}

.ai-page-baseline-feature-heading,
.ai-page-baseline-deviation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ai-page-baseline-feature-heading > strong {
  color: var(--color-text);
  font-size: 11px;
}

.ai-page-baseline-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 13px;
}

.ai-page-baseline-metrics > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.ai-page-baseline-metrics span,
.ai-page-baseline-deviation > span {
  color: var(--color-text-muted);
  font-size: 9px;
}

.ai-page-baseline-metrics strong {
  color: var(--color-text);
  font-size: 11px;
  overflow-wrap: anywhere;
}

.ai-page-baseline-deviation {
  padding-top: 10px;
  margin-top: 11px;
  border-top: 1px solid var(--color-border);
}

.ai-page-baseline-feature > p {
  margin: 9px 0 0;
  color: var(--color-text-secondary);
  font-size: 10px;
  line-height: 1.5;
}

.ai-page-baseline-notice {
  margin-top: 12px;
  padding: 11px;
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-radius: 8px;
  background: rgba(245, 158, 11, 0.06);
  color: var(--color-text-secondary);
  font-size: 10px;
  line-height: 1.6;
}

.ai-page-baseline-disclaimer {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: 13px;
  color: var(--color-text-muted);
  font-size: 10px;
}

.ai-page-baseline-disclaimer svg {
  flex-shrink: 0;
  color: var(--color-info);
}

.ai-page-status-deviation,
.ai-page-status-anomaly {
  color: #F87171;
  background: rgba(239, 68, 68, 0.13);
}

.ai-page-status-within-baseline,
.ai-page-status-normal {
  color: #4ADE80;
  background: rgba(34, 197, 94, 0.13);
}

.ai-page-status-zero-mad,
.ai-page-status-insufficient-variability,
.ai-page-status-invalid-reading,
.ai-page-status-not-evaluated {
  color: #FBBF24;
  background: rgba(245, 158, 11, 0.13);
}

@media (max-width: 600px) {
  .ai-page-baseline-grid {
    grid-template-columns: 1fr;
  }
}
"""

css = css_path.read_text(encoding="utf-8-sig")

if "/* Three-layer AI intelligence results */" not in css:
    css_path.write_text(css.rstrip() + "\n" + css_addition, encoding="utf-8")

print("AI INTELLIGENCE THREE-LAYER UI UPDATED")
print("Rule-Based Analysis panel added")
print("Isolation Forest result panel preserved")
print("Personal Baseline feature comparison added")
print("API response validation updated")
print("Responsive CSS added")
