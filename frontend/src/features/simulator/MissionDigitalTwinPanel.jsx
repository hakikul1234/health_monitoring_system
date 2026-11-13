import { useCallback, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Clock3,
  Database,
  HeartPulse,
  Leaf,
  RefreshCw,
  ShieldAlert,
  BrainCircuit,
  Microscope,
  Users,
  Waves,
} from "lucide-react";

import { getMissionDigitalTwinSummary } from "./missionDigitalTwinService";
import "./MissionDigitalTwinPanel.css";

function formatDate(value) {
  if (!value) return "--";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "--";

  return date.toLocaleString();
}

function formatValue(value, suffix = "", digits = 1) {
  if (value === null || value === undefined || value === "") {
    return "--";
  }

  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) return "--";

  return `${numericValue.toFixed(digits)}${suffix}`;
}

function MetricCard({ label, value, detail, icon: Icon, tone = "blue" }) {
  return (
    <article className={`dt-metric-card dt-tone-${tone}`}>
      <div className="dt-metric-top">
        <span>{label}</span>
        <Icon size={19} />
      </div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function QualityCounts({ counts }) {
  const items = [
    ["VALID", counts?.VALID ?? 0],
    ["SUSPECT", counts?.SUSPECT ?? 0],
    ["UNGRADABLE", counts?.UNGRADABLE ?? 0],
  ];

  return (
    <div className="dt-quality-list">
      {items.map(([label, value]) => (
        <div className="dt-quality-item" key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}

function MissionDigitalTwinPanel({ missions = [] }) {
  const [selectedMissionId, setSelectedMissionId] = useState("");
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const sortedMissions = useMemo(
    () =>
      [...missions].sort((a, b) =>
        String(a.mission_code || "").localeCompare(
          String(b.mission_code || "")
        )
      ),
    [missions]
  );


  const loadSummary = useCallback(async () => {
    if (!selectedMissionId) {
      setSummary(null);
      setError("Select a mission to open its Digital Twin.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await getMissionDigitalTwinSummary(selectedMissionId);
      setSummary(data);
    } catch (requestError) {
      setSummary(null);
      setError(
        requestError?.response?.data?.message ||
        requestError?.message ||
        "Unable to retrieve the mission snapshot."
      );
    } finally {
      setLoading(false);
    }
  }, [selectedMissionId]);


  const mission = summary?.mission;
  const crew = summary?.crew_health;
  const habitat = summary?.habitat;
  const alerts = summary?.health_alerts;
  const provenance = summary?.data_provenance;
  const averages = habitat?.averages || {};
  const xai = summary?.explainable_intelligence;
  const assessment = xai?.mission_assessment;
  const crewFindings = xai?.crew_findings;
  const habitatFindings = xai?.habitat_findings;
  const audit = xai?.audit_summary;

  return (
    <section className="mission-digital-twin">
      <div className="dt-heading">
        <div>
          <span className="dt-eyebrow">
            <Activity size={13} />
            MISSION INTELLIGENCE
          </span>
          <h2>Mission Digital Twin</h2>
          <p>
            Unified snapshot of stored crew health, habitat telemetry and
            mission-linked alerts.
          </p>
        </div>

        <span className="dt-readonly-tag">
          <Database size={13} />
          READ ONLY
        </span>
      </div>

      <div className="dt-selector">
        <div className="dt-selector-field">
          <label htmlFor="dt-mission-select">Select mission</label>
          <select
            id="dt-mission-select"
            value={selectedMissionId}
            onChange={(event) => {
              setSelectedMissionId(event.target.value);
              setSummary(null);
              setError("");
            }}
          >
            <option value="">Choose a mission...</option>
            {sortedMissions.map((item) => (
              <option key={item.id} value={item.id}>
                {item.mission_code || `MISSION-${item.id}`}
                {" · "}
                {item.mission_name || "Unnamed mission"}
              </option>
            ))}
          </select>
        </div>

        <button
          type="button"
          className="dt-refresh-button"
          onClick={loadSummary}
          disabled={!selectedMissionId || loading}
        >
          <RefreshCw size={16} className={loading ? "dt-spinning" : ""} />
          {loading ? "Loading..." : "Load snapshot"}
        </button>
      </div>

      {!selectedMissionId && (
        <div className="dt-empty-state">
          <Waves size={25} />
          <strong>No mission selected</strong>
          <span>
            Select a mission to inspect its combined crew and habitat records.
          </span>
        </div>
      )}

      {error && selectedMissionId && (
        <div className="dt-error-state" role="alert">
          <AlertTriangle size={17} />
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="dt-loading-state" role="status">
          <RefreshCw size={19} className="dt-spinning" />
          Retrieving stored mission records...
        </div>
      )}

      {summary && !loading && (
        <div className="dt-content">
          <div className="dt-mission-banner">
            <div>
              <span className="dt-label">MISSION IDENTIFICATION</span>
              <h3>{mission?.mission_name || "Mission"}</h3>
              <p>
                {mission?.mission_code || "--"}
                {" · "}
                {mission?.mission_type || "--"}
                {" · "}
                {mission?.destination || "Destination not specified"}
              </p>
            </div>
            <span className="dt-status">
              {mission?.status || "UNKNOWN"}
            </span>
          </div>

          <div className="dt-metric-grid">
            <MetricCard
              label="Crew readings"
              value={crew?.total_readings ?? 0}
              detail="Stored physiological records"
              icon={HeartPulse}
              tone="blue"
            />
            <MetricCard
              label="Habitat readings"
              value={habitat?.total_readings ?? 0}
              detail="Stored environmental records"
              icon={Waves}
              tone="cyan"
            />
            <MetricCard
              label="Open alerts"
              value={alerts?.open ?? 0}
              detail={`${alerts?.critical_open ?? 0} critical open`}
              icon={ShieldAlert}
              tone="orange"
            />
            <MetricCard
              label="Crew members"
              value={mission?.crew_count ?? 0}
              detail="Assigned to this mission"
              icon={Users}
              tone="violet"
            />
          </div>

          <div className="dt-section-grid">
            <article className="dt-data-panel">
              <div className="dt-panel-heading">
                <HeartPulse size={18} />
                <div>
                  <h3>Crew Health Intelligence</h3>
                  <p>Latest stored physiological readings</p>
                </div>
              </div>

              <QualityCounts counts={crew?.data_quality_counts} />

              <div className="dt-record-list">
                {(crew?.latest_readings || []).length === 0 ? (
                  <p className="dt-no-records">No crew readings available.</p>
                ) : (
                  crew.latest_readings.map((reading) => (
                    <div className="dt-record-row" key={reading.id}>
                      <div>
                        <strong>{reading.astronaut_name || "Crew member"}</strong>
                        <small>
                          {reading.astronaut_code || "--"}
                          {" · "}
                          {formatDate(reading.recorded_at)}
                        </small>
                      </div>
                      <span className="dt-record-value">
                        {reading.heart_rate_bpm ?? "--"} BPM
                      </span>
                    </div>
                  ))
                )}
              </div>
            </article>

            <article className="dt-data-panel">
              <div className="dt-panel-heading">
                <Leaf size={18} />
                <div>
                  <h3>Habitat Intelligence</h3>
                  <p>Stored measurement averages</p>
                </div>
              </div>

              <div className="dt-environment-grid">
                <div>
                  <span>Oxygen partial pressure</span>
                  <strong>
                    {formatValue(
                      averages.oxygen_partial_pressure_kpa,
                      " kPa"
                    )}
                  </strong>
                </div>
                <div>
                  <span>Carbon dioxide</span>
                  <strong>
                    {formatValue(averages.carbon_dioxide_ppm, " ppm", 0)}
                  </strong>
                </div>
                <div>
                  <span>Cabin pressure</span>
                  <strong>
                    {formatValue(averages.cabin_pressure_kpa, " kPa")}
                  </strong>
                </div>
                <div>
                  <span>Cabin temperature</span>
                  <strong>
                    {formatValue(averages.cabin_temperature_c, " °C")}
                  </strong>
                </div>
                <div>
                  <span>Relative humidity</span>
                  <strong>
                    {formatValue(averages.relative_humidity_percent, "%")}
                  </strong>
                </div>
              </div>

              <QualityCounts counts={habitat?.data_quality_counts} />
            </article>
          </div>

          <article className="dt-data-panel dt-alert-panel">
            <div className="dt-panel-heading">
              <ShieldAlert size={18} />
              <div>
                <h3>Crew Health Alerts</h3>
                <p>
                  Alerts linked to health readings for this mission only
                </p>
              </div>
            </div>

            {(alerts?.latest || []).length === 0 ? (
              <p className="dt-no-records">No mission-linked health alerts.</p>
            ) : (
              <div className="dt-record-list">
                {alerts.latest.map((alert) => (
                  <div className="dt-record-row" key={alert.id}>
                    <div>
                      <strong>
                        {alert.parameter || "Health parameter"}
                        {" · "}
                        {alert.astronaut_name || "Crew member"}
                      </strong>
                      <small>
                        {alert.explanation || alert.rule_code || "--"}
                      </small>
                    </div>
                    <span
                      className={`dt-alert-badge dt-alert-${String(
                        alert.severity || "warning"
                      ).toLowerCase()}`}
                    >
                      {alert.severity || "WARNING"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="dt-xai-panel">
            <div className="dt-panel-heading">
              <BrainCircuit size={19} />
              <div>
                <h3>Explainable Mission Intelligence</h3>
                <p>Evidence-linked explanations from persisted mission records</p>
              </div>
            </div>

            {assessment && (
              <div className="dt-xai-assessment">
                <div>
                  <span className="dt-label">MISSION ASSESSMENT</span>
                  <strong>{assessment.code || "UNAVAILABLE"}</strong>
                  <p>{assessment.summary || "No assessment summary available."}</p>
                </div>
                <span className="dt-xai-status">
                  INFORMATIONAL ONLY
                </span>
              </div>
            )}

            <div className="dt-xai-grid">
              <section className="dt-xai-subpanel">
                <div className="dt-xai-subheading">
                  <HeartPulse size={16} />
                  <h4>Crew Evidence</h4>
                  <span>{crewFindings?.total_alerts ?? 0} alerts</span>
                </div>

                <p className="dt-xai-description">
                  Explanations are sourced from persisted HealthAlert records.
                </p>

                {(crewFindings?.items || []).length === 0 ? (
                  <p className="dt-no-records">No crew evidence available.</p>
                ) : (
                  crewFindings.items.map((finding) => (
                    <div
                      className="dt-xai-evidence"
                      key={`crew-${finding.source_record_id}`}
                    >
                      <div className="dt-xai-evidence-top">
                        <strong>
                          {finding.parameter || "Health parameter"}
                          {" · "}
                          {finding.astronaut_name || "Crew member"}
                        </strong>
                        <span className={`dt-alert-badge dt-alert-${String(
                          finding.severity || "warning"
                        ).toLowerCase()}`}>
                          {finding.severity || "UNKNOWN"}
                        </span>
                      </div>
                      <p>{finding.explanation || "No explanation stored."}</p>
                      <small>
                        Alert #{finding.source_record_id}
                        {" · "}
                        Reading #{finding.reading_id}
                        {" · "}
                        {formatDate(finding.recorded_at)}
                      </small>
                      <small>
                        Status: {finding.status || "--"}
                        {" · "}
                        {finding.is_synthetic ? "SYNTHETIC" : "NON-SYNTHETIC"}
                      </small>
                    </div>
                  ))
                )}
              </section>

              <section className="dt-xai-subpanel">
                <div className="dt-xai-subheading">
                  <Microscope size={16} />
                  <h4>Habitat Evidence</h4>
                  <span>{habitatFindings?.suspect_records_available ?? 0} suspect</span>
                </div>

                <p className="dt-xai-description">
                  Scenario-linked observations, not validated spacecraft limits.
                </p>

                <QualityCounts counts={habitatFindings?.quality_counts} />

                {(habitatFindings?.items || []).length === 0 ? (
                  <p className="dt-no-records">
                    No SUSPECT habitat observations available.
                  </p>
                ) : (
                  habitatFindings.items.map((finding) => (
                    <div
                      className="dt-xai-evidence"
                      key={`habitat-${finding.source_record_id}`}
                    >
                      <div className="dt-xai-evidence-top">
                        <strong>{finding.scenario || "Habitat scenario"}</strong>
                        <span className="dt-xai-quality">
                          {finding.data_quality || "UNKNOWN"}
                        </span>
                      </div>
                      <p>{finding.scenario_description}</p>
                      <p>{finding.explanation}</p>
                      <div className="dt-xai-observations">
                        <span>O₂: {formatValue(
                          finding.observations?.oxygen_partial_pressure_kpa,
                          " kPa"
                        )}</span>
                        <span>CO₂: {formatValue(
                          finding.observations?.carbon_dioxide_ppm,
                          " ppm",
                          0
                        )}</span>
                        <span>Pressure: {formatValue(
                          finding.observations?.cabin_pressure_kpa,
                          " kPa"
                        )}</span>
                        <span>Temperature: {formatValue(
                          finding.observations?.cabin_temperature_c,
                          " °C"
                        )}</span>
                        <span>Humidity: {formatValue(
                          finding.observations?.relative_humidity_percent,
                          "%"
                        )}</span>
                      </div>
                      <small>
                        Sensor: {finding.sensor_id || "--"}
                        {" · "}
                        Record #{finding.source_record_id}
                        {" · "}
                        {formatDate(finding.recorded_at)}
                      </small>
                      <small>
                        {finding.is_synthetic ? "SYNTHETIC" : "NON-SYNTHETIC"}
                      </small>
                    </div>
                  ))
                )}
              </section>
            </div>

            {audit && (
              <section className="dt-audit-panel">
                <div className="dt-audit-heading">
                  <div>
                    <span className="dt-label">EVIDENCE TRACEABILITY</span>
                    <h4>Mission Evidence Audit</h4>
                    <p>
                      Source-level record accounting and retrieval transparency
                    </p>
                  </div>
                  <span className="dt-audit-tag">READ ONLY AUDIT</span>
                </div>

                <div className="dt-audit-metrics">
                  <div>
                    <span>Total unique evidence</span>
                    <strong>
                      {audit.record_counts?.total_evidence_records ?? 0}
                    </strong>
                  </div>
                  <div>
                    <span>Synthetic records</span>
                    <strong>
                      {audit.record_counts?.synthetic_records ?? 0}
                    </strong>
                  </div>
                  <div>
                    <span>Non-synthetic records</span>
                    <strong>
                      {audit.record_counts?.non_synthetic_records ?? 0}
                    </strong>
                  </div>
                </div>

                <div className="dt-audit-source-grid">
                  <div>
                    <span>Crew health alerts</span>
                    <strong>
                      {audit.source_counts?.crew_health_alerts ?? 0}
                    </strong>
                  </div>
                  <div>
                    <span>Habitat telemetry</span>
                    <strong>
                      {audit.source_counts?.habitat_telemetry ?? 0}
                    </strong>
                  </div>
                </div>

                <div className="dt-audit-retrieval">
                  <strong>Evidence retrieval coverage</strong>

                  {[
                    ["Crew findings", audit.retrieval?.crew_findings],
                    [
                      "Habitat suspect findings",
                      audit.retrieval?.habitat_suspect_findings,
                    ],
                  ].map(([label, item]) => (
                    <div className="dt-audit-retrieval-row" key={label}>
                      <span>{label}</span>
                      <strong>
                        {item?.returned ?? 0} / {item?.available ?? 0}
                        {" returned"}
                      </strong>
                      <small>
                        Limit: {item?.limit ?? 0}
                        {" ? "}
                        {item?.truncated
                          ? "Additional records not displayed"
                          : "All available findings returned"}
                      </small>
                    </div>
                  ))}
                </div>

                {Object.values(audit.retrieval || {}).some(
                  (item) => item?.truncated
                ) && (
                  <div className="dt-audit-warning" role="status">
                    <AlertTriangle size={15} />
                    Some evidence records exceed the display limit.
                    The audit counts include available source records.
                  </div>
                )}

                <div className="dt-audit-timestamp">
                  <Clock3 size={14} />
                  Audit generated: {formatDate(audit.audit_generated_at)}
                </div>

                <p className="dt-audit-scope">
                  {audit.record_scope}
                </p>
              </section>
            )}

            <div className="dt-xai-policy">
              <strong>Evidence and interpretation policy</strong>
              <p>
                {xai?.evidence_policy?.ungradable_policy ||
                  "UNGRADABLE habitat measurements are not interpreted."}
              </p>
              <p>
                {xai?.evidence_policy?.synthetic_data_warning ||
                  "Synthetic simulator records are illustrative data only."}
              </p>
              <small>
                {xai?.disclaimer ||
                  "Research explainability output only. Not a medical diagnosis or operational decision."}
              </small>
            </div>
          </article>

          <article className="dt-provenance-panel">
            <div className="dt-panel-heading">
              <Database size={18} />
              <div>
                <h3>Data Provenance</h3>
                <p>Origin and quality context for included records</p>
              </div>
            </div>

            <div className="dt-provenance-grid">
              <div>
                <span>Total included records</span>
                <strong>{provenance?.total_records ?? 0}</strong>
              </div>
              <div>
                <span>Synthetic records</span>
                <strong>{provenance?.synthetic_records ?? 0}</strong>
              </div>
              <div>
                <span>Non-synthetic records</span>
                <strong>{provenance?.non_synthetic_records ?? 0}</strong>
              </div>
              <div>
                <span>All records synthetic</span>
                <strong>
                  {provenance?.all_synthetic === null
                    ? "NO DATA"
                    : provenance?.all_synthetic
                      ? "YES"
                      : "NO"}
                </strong>
              </div>
            </div>

            <div className="dt-last-updated">
              <Clock3 size={14} />
              Crew: {formatDate(crew?.latest_reading_at)}
              {" · "}
              Habitat: {formatDate(habitat?.latest_reading_at)}
            </div>
          </article>

          <div className="dt-disclaimer">
            <AlertTriangle size={17} />
            <p>
              {summary.disclaimer ||
                "Research software demonstration only. Not a real-time spacecraft safety assessment or medical diagnosis."}
            </p>
          </div>
        </div>
      )}

      {!selectedMissionId && sortedMissions.length === 0 && (
        <div className="dt-mission-hint">
          No missions are currently available in the simulator.
        </div>
      )}
    </section>
  );
}

export default MissionDigitalTwinPanel;
