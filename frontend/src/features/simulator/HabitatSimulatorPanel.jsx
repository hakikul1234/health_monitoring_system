import { useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Database,
  Gauge,
  Play,
  Radio,
  RefreshCw,
  ShieldAlert,
  Thermometer,
  Waves,
  Wind,
} from "lucide-react";

import {
  HABITAT_SCENARIOS,
  generateHabitatTelemetry,
} from "./habitatService";

import "./HabitatSimulatorPanel.css";

function displayMetric(value, suffix = "") {
  if (value === null || value === undefined || value === "") {
    return "--";
  }

  if (typeof value === "number") {
    return `${Number(value.toFixed(2))}${suffix}`;
  }

  return `${value}${suffix}`;
}

function formatTimestamp(value) {
  if (!value) return "--";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "--";

  return date.toLocaleString();
}

function getErrorMessage(error) {
  const data = error.response?.data;

  if (data?.detail) return data.detail;
  if (data?.message) return data.message;

  if (data?.errors && typeof data.errors === "object") {
    const firstValue = Object.values(data.errors)[0];

    if (Array.isArray(firstValue)) {
      return String(firstValue[0]);
    }

    if (typeof firstValue === "string") {
      return firstValue;
    }
  }

  return error.message || "Habitat simulation request failed.";
}

function QualityBadge({ quality }) {
  const normalized = String(quality || "UNKNOWN").toLowerCase();

  return (
    <span className={`hab-quality-badge hab-quality-${normalized}`}>
      {quality || "UNKNOWN"}
    </span>
  );
}

function MetricCard({ icon: Icon, label, value, unit, description }) {
  return (
    <article className="hab-metric-card">
      <div className="hab-metric-icon">
        <Icon size={19} />
      </div>
      <span className="hab-metric-label">{label}</span>
      <strong className="hab-metric-value">
        {displayMetric(value, unit)}
      </strong>
      <small>{description}</small>
    </article>
  );
}

export default function HabitatSimulatorPanel({ missions = [] }) {
  const [missionId, setMissionId] = useState("");
  const [scenario, setScenario] = useState("NORMAL_HABITAT");
  const [sensorId, setSensorId] = useState("SIM-HAB-01");
  const [count, setCount] = useState("10");
  const [intervalSeconds, setIntervalSeconds] = useState("60");
  const [seed, setSeed] = useState("");

  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  const selectedScenario = useMemo(
    () => HABITAT_SCENARIOS.find((item) => item.id === scenario),
    [scenario]
  );

  const summary = result?.summary || {};
  const readings = result?.readings || [];
  const qualityCounts = summary.quality_counts || {};

  const allUngradable =
    readings.length > 0 &&
    readings.every((reading) => reading.data_quality === "UNGRADABLE");

  const handleGenerate = async (event) => {
    event.preventDefault();

    setError("");
    setSuccessMessage("");
    setResult(null);

    if (!missionId) {
      setError("Please select a mission.");
      return;
    }

    const parsedCount = Number(count);
    const parsedInterval = Number(intervalSeconds);
    const cleanSensorId = sensorId.trim();

    if (
      !Number.isInteger(parsedCount) ||
      parsedCount < 1 ||
      parsedCount > 1000
    ) {
      setError("Reading count must be between 1 and 1000.");
      return;
    }

    if (
      !Number.isInteger(parsedInterval) ||
      parsedInterval < 1 ||
      parsedInterval > 3600
    ) {
      setError("Interval must be between 1 and 3600 seconds.");
      return;
    }

    if (!cleanSensorId || cleanSensorId.length > 64) {
      setError("Sensor ID must contain 1 to 64 characters.");
      return;
    }

    const payload = {
      mission_id: Number(missionId),
      scenario,
      count: parsedCount,
      interval_seconds: parsedInterval,
      sensor_id: cleanSensorId,
    };

    if (seed.trim() !== "") {
      const parsedSeed = Number(seed);

      if (!Number.isSafeInteger(parsedSeed)) {
        setError("Seed must be a valid safe integer.");
        return;
      }

      payload.seed = parsedSeed;
    }

    setIsGenerating(true);

    try {
      const response = await generateHabitatTelemetry(payload);

      setResult(response);
      setSuccessMessage(
        response.message || "Habitat telemetry generated successfully."
      );
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setIsGenerating(false);
    }
  };

  const handleScenarioChange = (value) => {
    setScenario(value);
    setResult(null);
    setError("");
    setSuccessMessage("");
  };

  return (
    <section className="habitat-panel">
      <div className="habitat-heading">
        <div>
          <span className="habitat-eyebrow">
            <span />
            MISSION DIGITAL TWIN / ENVIRONMENTAL SYSTEMS
          </span>

          <h2>
            Habitat <span>Intelligence</span>
          </h2>

          <p>
            Generate synthetic cabin-environment telemetry and inspect
            sensor quality, environmental metrics and mission records.
          </p>
        </div>

        <div className="habitat-live-indicator">
          <Radio size={15} />
          SIMULATION MODULE
        </div>
      </div>

      <div className="habitat-disclaimer">
        <AlertTriangle size={19} />
        <div>
          <strong>Research prototype · Synthetic data only</strong>
          <p>
            These generated values are illustrative software test data.
            They are not real spacecraft telemetry, validated spacecraft
            operating limits, safety thresholds or environmental safety
            assessments.
          </p>
        </div>
      </div>

      <div className="habitat-section-heading">
        <div>
          <span className="habitat-section-label">01 / ENVIRONMENT SCENARIOS</span>
          <h3>Select habitat conditions</h3>
        </div>
        <span className="habitat-mode-count">05 AVAILABLE MODES</span>
      </div>

      <div className="habitat-scenario-grid">
        {HABITAT_SCENARIOS.map((item) => {
          const active = scenario === item.id;

          return (
            <button
              type="button"
              key={item.id}
              className={`habitat-scenario-card hab-tone-${item.tone} ${
                active ? "habitat-scenario-active" : ""
              }`}
              onClick={() => handleScenarioChange(item.id)}
              aria-pressed={active}
            >
              <div className="habitat-scenario-top">
                <Waves size={19} />
                {active && <CheckCircle2 size={17} />}
              </div>
              <strong>{item.name}</strong>
              <p>{item.description}</p>
            </button>
          );
        })}
      </div>

      <div className="habitat-config-layout">
        <form className="habitat-config-card" onSubmit={handleGenerate}>
          <div className="habitat-section-heading">
            <div>
              <span className="habitat-section-label">02 / SIMULATION CONFIGURATION</span>
              <h3>Generation parameters</h3>
            </div>
            <Gauge size={20} />
          </div>

          <div className="habitat-form-field">
            <label htmlFor="habitat-mission">Mission *</label>
            <select
              id="habitat-mission"
              value={missionId}
              onChange={(event) => setMissionId(event.target.value)}
              required
            >
              <option value="">Select mission</option>
              {missions.map((mission) => (
                <option key={mission.id} value={mission.id}>
                  {mission.mission_code || `MISSION-${mission.id}`}
                  {" · "}
                  {mission.mission_name || "Unnamed mission"}
                </option>
              ))}
            </select>
            <small>{missions.length} mission records available</small>
          </div>

          <div className="habitat-form-field">
            <label htmlFor="habitat-sensor">Sensor identifier *</label>
            <input
              id="habitat-sensor"
              type="text"
              maxLength={64}
              value={sensorId}
              onChange={(event) => setSensorId(event.target.value)}
              placeholder="SIM-HAB-01"
              required
            />
            <small>Maximum 64 characters</small>
          </div>

          <div className="habitat-form-row">
            <div className="habitat-form-field">
              <label htmlFor="habitat-count">Reading count *</label>
              <input
                id="habitat-count"
                type="number"
                min="1"
                max="1000"
                value={count}
                onChange={(event) => setCount(event.target.value)}
                required
              />
              <small>1–1000 readings</small>
            </div>

            <div className="habitat-form-field">
              <label htmlFor="habitat-interval">Interval (seconds) *</label>
              <input
                id="habitat-interval"
                type="number"
                min="1"
                max="3600"
                value={intervalSeconds}
                onChange={(event) => setIntervalSeconds(event.target.value)}
                required
              />
              <small>1–3600 seconds</small>
            </div>
          </div>

          <div className="habitat-form-field">
            <label htmlFor="habitat-seed">Reproducible random seed</label>
            <input
              id="habitat-seed"
              type="number"
              value={seed}
              onChange={(event) => setSeed(event.target.value)}
              placeholder="Optional · e.g. 2026"
            />
            <small>Reuse a seed to reproduce the same scenario sequence.</small>
          </div>

          {error && (
            <div className="habitat-message habitat-message-error" role="alert">
              <AlertTriangle size={16} />
              <span>{error}</span>
            </div>
          )}

          {successMessage && (
            <div className="habitat-message habitat-message-success" role="status">
              <CheckCircle2 size={16} />
              <span>{successMessage}</span>
            </div>
          )}

          <button
            className="habitat-generate-button"
            type="submit"
            disabled={isGenerating || missions.length === 0}
          >
            {isGenerating ? (
              <>
                <RefreshCw size={17} className="habitat-spin" />
                Generating habitat telemetry...
              </>
            ) : (
              <>
                <Play size={17} fill="currentColor" />
                Generate habitat telemetry
              </>
            )}
          </button>

          {missions.length === 0 && (
            <p className="habitat-empty-note">
              No missions are available. Create or assign a mission first.
            </p>
          )}
        </form>

        <aside className="habitat-context-card">
          <div className="habitat-context-icon">
            <Wind size={23} />
          </div>

          <span className="habitat-section-label">ACTIVE SCENARIO</span>
          <h3>{selectedScenario?.name || "Select scenario"}</h3>
          <p>{selectedScenario?.description}</p>

          <div className="habitat-context-divider" />

          <div className="habitat-context-item">
            <Database size={16} />
            <div>
              <span>Sensor identifier</span>
              <strong>{sensorId || "--"}</strong>
            </div>
          </div>

          <div className="habitat-context-item">
            <Activity size={16} />
            <div>
              <span>Sampling configuration</span>
              <strong>{count} readings · {intervalSeconds}s</strong>
            </div>
          </div>

          <div className="habitat-context-item">
            <Clock3 size={16} />
            <div>
              <span>Mission records</span>
              <strong>{missions.length} available</strong>
            </div>
          </div>

          <div className="habitat-context-note">
            <ShieldAlert size={16} />
            Synthetic environmental scenarios are intended for software
            testing and demonstration only.
          </div>
        </aside>
      </div>

      {result && (
        <section className="habitat-results">
          <div className="habitat-section-heading">
            <div>
              <span className="habitat-section-label">03 / ENVIRONMENTAL REPORT</span>
              <h3>Habitat telemetry results</h3>
            </div>
            <span className="habitat-complete-status">
              <CheckCircle2 size={15} />
              GENERATION COMPLETE
            </span>
          </div>

          <div className="habitat-result-overview">
            <div>
              <span>MISSION</span>
              <strong>
                {result.mission?.mission_code ||
                  result.mission?.mission_name ||
                  result.mission?.id ||
                  missionId}
              </strong>
            </div>
            <div>
              <span>SCENARIO</span>
              <strong>{result.scenario || scenario}</strong>
            </div>
            <div>
              <span>SENSOR</span>
              <strong>{result.sensor_id || sensorId}</strong>
            </div>
            <div>
              <span>TOTAL RECORDS</span>
              <strong>{summary.total_readings ?? readings.length}</strong>
            </div>
          </div>

          <div className="habitat-section-heading habitat-metrics-heading">
            <div>
              <span className="habitat-section-label">04 / ENVIRONMENT METRICS</span>
              <h3>Gradeable data averages</h3>
            </div>
            {allUngradable && (
              <span className="habitat-no-gradeable">
                NO GRADEABLE DATA
              </span>
            )}
          </div>

          {allUngradable && (
            <div className="habitat-quality-warning">
              <AlertTriangle size={17} />
              All returned readings are UNGRADABLE. Placeholder values
              are excluded from environmental averages and must not be
              interpreted as measurements.
            </div>
          )}

          <div className="habitat-metric-grid">
            <MetricCard
              icon={Wind}
              label="Oxygen partial pressure"
              value={summary.average_oxygen_partial_pressure_kpa}
              unit=" kPa"
              description="Average of usable records"
            />
            <MetricCard
              icon={Activity}
              label="Carbon dioxide"
              value={summary.average_carbon_dioxide_ppm}
              unit=" ppm"
              description="Average of usable records"
            />
            <MetricCard
              icon={Gauge}
              label="Cabin pressure"
              value={summary.average_cabin_pressure_kpa}
              unit=" kPa"
              description="Average of usable records"
            />
            <MetricCard
              icon={Thermometer}
              label="Cabin temperature"
              value={summary.average_cabin_temperature_c}
              unit=" °C"
              description="Average of usable records"
            />
            <MetricCard
              icon={Waves}
              label="Relative humidity"
              value={summary.average_relative_humidity_percent}
              unit="%"
              description="Average of usable records"
            />
          </div>

          <div className="habitat-quality-summary">
            <div className="habitat-section-heading">
              <div>
                <span className="habitat-section-label">05 / SENSOR QUALITY</span>
                <h3>Data quality distribution</h3>
              </div>
            </div>

            <div className="habitat-quality-grid">
              {["VALID", "SUSPECT", "UNGRADABLE"].map((quality) => (
                <div className="habitat-quality-item" key={quality}>
                  <QualityBadge quality={quality} />
                  <strong>{qualityCounts[quality] ?? 0}</strong>
                  <span>records</span>
                </div>
              ))}
            </div>
          </div>

          <div className="habitat-results-panel">
            <div className="habitat-results-panel-heading">
              <div>
                <h3>Environmental telemetry records</h3>
                <p>
                  {result.scenario_description || selectedScenario?.description}
                </p>
              </div>
              <span>{readings.length} RECORDS</span>
            </div>

            {readings.length === 0 ? (
              <div className="habitat-empty-note">
                No telemetry records were returned.
              </div>
            ) : (
              <div className="habitat-table-scroll">
                <table className="habitat-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Oxygen kPa</th>
                      <th>CO2 ppm</th>
                      <th>Pressure kPa</th>
                      <th>Temperature °C</th>
                      <th>Humidity %</th>
                      <th>Quality</th>
                      <th>Recorded at</th>
                    </tr>
                  </thead>
                  <tbody>
                    {readings.map((reading) => (
                      <tr key={reading.id}>
                        <td>#{reading.id}</td>
                        <td>{displayMetric(reading.oxygen_partial_pressure_kpa)}</td>
                        <td>{displayMetric(reading.carbon_dioxide_ppm)}</td>
                        <td>{displayMetric(reading.cabin_pressure_kpa)}</td>
                        <td>{displayMetric(reading.cabin_temperature_c)}</td>
                        <td>{displayMetric(reading.relative_humidity_percent)}</td>
                        <td>
                          <QualityBadge quality={reading.data_quality} />
                        </td>
                        <td>{formatTimestamp(reading.recorded_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="habitat-result-timestamps">
            <div>
              <span>FIRST RECORD</span>
              <strong>{formatTimestamp(summary.first_recorded_at)}</strong>
            </div>
            <div>
              <span>LAST RECORD</span>
              <strong>{formatTimestamp(summary.last_recorded_at)}</strong>
            </div>
          </div>

          <div className="habitat-result-disclaimer">
            <AlertTriangle size={16} />
            {result.disclaimer ||
              "Synthetic environmental data only. Not for spacecraft operations or safety decisions."}
          </div>
        </section>
      )}
    </section>
  );
}
