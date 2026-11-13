import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Cpu,
  HeartPulse,
  Play,
  Radio,
  RefreshCw,
  ShieldAlert,
  Users,
  Waves,
  Zap,
} from "lucide-react";

import useAuthStore from "../../stores/authStore";
import useSimulatorStore from "./simulatorStore";
import HabitatSimulatorPanel from "./HabitatSimulatorPanel";
import MissionDigitalTwinPanel from "./MissionDigitalTwinPanel";
import "./SimulatorPage.css";

const SCENARIOS = [
  {
    id: "NORMAL_MISSION",
    name: "Normal Mission",
    description: "Generate stable synthetic mission telemetry.",
    icon: Activity,
    tone: "normal",
    quality: "VALID",
  },
  {
    id: "HEALTH_ANOMALY",
    name: "Health Anomaly",
    description: "Simulate elevated and unusual vital-sign patterns.",
    icon: HeartPulse,
    tone: "warning",
    quality: "SUSPECT",
  },
  {
    id: "EMERGENCY_MISSION",
    name: "Emergency Mission",
    description: "Generate high-severity synthetic demonstration data.",
    icon: ShieldAlert,
    tone: "critical",
    quality: "SUSPECT",
  },
  {
    id: "DATA_QUALITY_FAULT",
    name: "Data Quality Fault",
    description: "Simulate ungradable readings and quality issues.",
    icon: Radio,
    tone: "fault",
    quality: "UNGRADABLE",
  },
];

function formatDate(value) {
  if (!value) return "--";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "--";

  return date.toLocaleString();
}

function displayValue(value) {
  if (value === null || value === undefined || value === "") {
    return "--";
  }

  return String(value);
}

function getAstronautName(astronaut) {
  return (
    astronaut?.profile?.full_name ||
    astronaut?.full_name ||
    astronaut?.call_sign ||
    astronaut?.astronaut_code ||
    `Astronaut #${astronaut?.id}`
  );
}

function getErrorText(error) {
  return (
    error?.response?.data?.message ||
    error?.message ||
    "Unable to complete simulator request."
  );
}

function SimulatorPage() {
  const user = useAuthStore((state) => state.user);

  const astronauts = useSimulatorStore((state) => state.astronauts);
  const missions = useSimulatorStore((state) => state.missions);
  const result = useSimulatorStore((state) => state.generationResult);
  const isLoadingOptions = useSimulatorStore(
    (state) => state.isLoadingOptions
  );
  const isGenerating = useSimulatorStore(
    (state) => state.isGenerating
  );
  const storeError = useSimulatorStore((state) => state.error);

  const fetchSimulatorOptions = useSimulatorStore(
    (state) => state.fetchSimulatorOptions
  );
  const runSimulation = useSimulatorStore(
    (state) => state.runSimulation
  );
  const clearGenerationResult = useSimulatorStore(
    (state) => state.clearGenerationResult
  );

  const [astronautId, setAstronautId] = useState("");
  const [missionId, setMissionId] = useState("");
  const [scenario, setScenario] = useState("NORMAL_MISSION");
  const [count, setCount] = useState(10);
  const [intervalSeconds, setIntervalSeconds] = useState(60);
  const [seed, setSeed] = useState("");
  const [formError, setFormError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const canControlSimulator = [
    "MISSION_CONTROL",
    "SYSTEM_ADMIN",
  ].includes(user?.role);

  useEffect(() => {
    if (canControlSimulator) {
      fetchSimulatorOptions().catch(() => {});
    }
  }, [canControlSimulator, fetchSimulatorOptions]);

  const selectedAstronaut = useMemo(
    () => astronauts.find(
      (item) => String(item.id) === String(astronautId)
    ),
    [astronauts, astronautId]
  );

  const availableMissions = useMemo(() => {
    if (!astronautId) return [];

    return missions.filter((mission) =>
      Array.isArray(mission.crew) &&
      mission.crew.some(
        (member) => String(member.id) === String(astronautId)
      )
    );
  }, [missions, astronautId]);

  const selectedScenario = SCENARIOS.find(
    (item) => item.id === scenario
  );

  const readings = result?.readings || [];
  const summary = result?.summary || {};
  const alertGeneration = result?.alert_generation || {};

  const handleAstronautChange = (value) => {
    setAstronautId(value);
    setMissionId("");
    setFormError("");
    setSuccessMessage("");
    clearGenerationResult();
  };

  const handleGenerate = async (event) => {
    event.preventDefault();

    setFormError("");
    setSuccessMessage("");

    if (!canControlSimulator) {
      setFormError("Your account cannot control the simulator.");
      return;
    }

    if (!astronautId) {
      setFormError("Please select an astronaut.");
      return;
    }

    if (!scenario) {
      setFormError("Please select a simulation scenario.");
      return;
    }

    const parsedCount = Number(count);
    const parsedInterval = Number(intervalSeconds);

    if (
      !Number.isInteger(parsedCount) ||
      parsedCount < 1 ||
      parsedCount > 1000
    ) {
      setFormError("Reading count must be between 1 and 1000.");
      return;
    }

    if (
      !Number.isInteger(parsedInterval) ||
      parsedInterval < 1 ||
      parsedInterval > 3600
    ) {
      setFormError("Interval must be between 1 and 3600 seconds.");
      return;
    }

    const payload = {
      astronaut_id: Number(astronautId),
      mission_id: missionId ? Number(missionId) : null,
      scenario,
      count: parsedCount,
      interval_seconds: parsedInterval,
    };

    if (seed.trim() !== "") {
      const parsedSeed = Number(seed);

      if (!Number.isInteger(parsedSeed)) {
        setFormError("Seed must be a valid integer.");
        return;
      }

      payload.seed = parsedSeed;
    }

    try {
      const response = await runSimulation(payload);

      setSuccessMessage(
        response?.message ||
        "Synthetic telemetry generated successfully."
      );
    } catch (error) {
      setFormError(getErrorText(error));
    }
  };

  const handleRefresh = () => {
    setFormError("");
    setSuccessMessage("");
    fetchSimulatorOptions().catch(() => {});
  };

  if (!canControlSimulator) {
    return (
      <div className="page-container sim-page">
        <div className="sim-access-denied">
          <ShieldAlert size={34} />
          <h2>Simulator access restricted</h2>
          <p>
            Only Mission Control and System Administrator roles
            can generate synthetic telemetry.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container sim-page">
      <section className="sim-heading">
        <div>
          <span className="sim-eyebrow">
            <span /> MISSION SYSTEMS / SIMULATION ENGINE
          </span>

          <h1>
            Telemetry <span>Simulator</span>
          </h1>

          <p>
            Generate controlled synthetic crew-health telemetry
            and inspect the resulting demonstration alerts.
          </p>
        </div>

        <button
          className="sim-secondary-button"
          type="button"
          onClick={handleRefresh}
          disabled={isLoadingOptions}
        >
          <RefreshCw
            size={15}
            className={isLoadingOptions ? "sim-spinning" : ""}
          />
          Refresh data
        </button>
      </section>

      <div className="sim-disclaimer">
        <AlertTriangle size={19} />
        <div>
          <strong>Software research prototype Â· Synthetic data only</strong>
          <p>
            This simulator does not collect real astronaut telemetry.
            Generated readings and alerts are for software demonstration
            and testing only, not clinical or operational decisions.
            Human review is required.
          </p>
        </div>
      </div>

      <section className="sim-scenario-section">
        <div className="sim-section-heading">
          <div>
            <span className="sim-section-label">01 / SCENARIO SELECTION</span>
            <h2>Choose mission conditions</h2>
          </div>
          <span className="sim-count-label">4 AVAILABLE MODES</span>
        </div>

        <div className="sim-scenario-grid">
          {SCENARIOS.map((item) => {
            const Icon = item.icon;
            const active = scenario === item.id;

            return (
              <button
                key={item.id}
                type="button"
                className={`sim-scenario-card sim-tone-${item.tone} ${
                  active ? "sim-scenario-active" : ""
                }`}
                onClick={() => {
                  setScenario(item.id);
                  setFormError("");
                  setSuccessMessage("");
                  clearGenerationResult();
                }}
                aria-pressed={active}
              >
                <div className="sim-scenario-top">
                  <div className="sim-scenario-icon">
                    <Icon size={21} />
                  </div>
                  {active && <CheckCircle2 size={18} />}
                </div>

                <strong>{item.name}</strong>
                <p>{item.description}</p>

                <span className="sim-quality-tag">
                  DATA QUALITY: {item.quality}
                </span>
              </button>
            );
          })}
        </div>
      </section>

      <section className="sim-config-layout">
        <form className="sim-config-card" onSubmit={handleGenerate}>
          <div className="sim-section-heading">
            <div>
              <span className="sim-section-label">02 / CONFIGURATION</span>
              <h2>Simulation parameters</h2>
            </div>
            <Cpu size={20} />
          </div>

          {isLoadingOptions ? (
            <div className="sim-inline-state">
              <RefreshCw size={18} className="sim-spinning" />
              Loading astronauts and missions...
            </div>
          ) : (
            <>
              <div className="sim-form-field">
                <label htmlFor="sim-astronaut">Astronaut *</label>
                <select
                  id="sim-astronaut"
                  value={astronautId}
                  onChange={(event) =>
                    handleAstronautChange(event.target.value)
                  }
                  required
                >
                  <option value="">Select astronaut</option>
                  {astronauts.map((astronaut) => (
                    <option key={astronaut.id} value={astronaut.id}>
                      {getAstronautName(astronaut)} Â· {astronaut.astronaut_code}
                    </option>
                  ))}
                </select>
                <small>
                  {astronauts.length} astronaut profiles available
                </small>
              </div>

              <div className="sim-form-field">
                <label htmlFor="sim-mission">Assigned mission</label>
                <select
                  id="sim-mission"
                  value={missionId}
                  onChange={(event) => setMissionId(event.target.value)}
                  disabled={!astronautId || availableMissions.length === 0}
                >
                  <option value="">
                    {astronautId
                      ? "No mission / standalone simulation"
                      : "Select astronaut first"}
                  </option>

                  {availableMissions.map((mission) => (
                    <option key={mission.id} value={mission.id}>
                      {mission.mission_code} Â· {mission.mission_name}
                    </option>
                  ))}
                </select>
                <small>
                  {astronautId
                    ? `${availableMissions.length} assigned missions available`
                    : "Choose an astronaut to view assigned missions"}
                </small>
              </div>

              <div className="sim-form-row">
                <div className="sim-form-field">
                  <label htmlFor="sim-count">Reading count *</label>
                  <input
                    id="sim-count"
                    type="number"
                    min="1"
                    max="1000"
                    value={count}
                    onChange={(event) => setCount(event.target.value)}
                    required
                  />
                  <small>Maximum 1000 readings</small>
                </div>

                <div className="sim-form-field">
                  <label htmlFor="sim-interval">Interval (seconds) *</label>
                  <input
                    id="sim-interval"
                    type="number"
                    min="1"
                    max="3600"
                    value={intervalSeconds}
                    onChange={(event) =>
                      setIntervalSeconds(event.target.value)
                    }
                    required
                  />
                  <small>1 to 3600 seconds</small>
                </div>
              </div>

              <div className="sim-form-field">
                <label htmlFor="sim-seed">Random seed (optional)</label>
                <input
                  id="sim-seed"
                  type="number"
                  placeholder="e.g. 2026"
                  value={seed}
                  onChange={(event) => setSeed(event.target.value)}
                />
                <small>
                  Use the same seed to reproduce generated values.
                </small>
              </div>
            </>
          )}

          {formError && (
            <div className="sim-message sim-message-error" role="alert">
              <AlertTriangle size={17} />
              <span>{formError}</span>
            </div>
          )}

          {storeError && !formError && (
            <div className="sim-message sim-message-error" role="alert">
              <AlertTriangle size={17} />
              <span>{storeError}</span>
            </div>
          )}

          {successMessage && (
            <div className="sim-message sim-message-success" role="status">
              <CheckCircle2 size={17} />
              <span>{successMessage}</span>
            </div>
          )}

          <button
            className="sim-generate-button"
            type="submit"
            disabled={
              isGenerating ||
              isLoadingOptions ||
              astronauts.length === 0
            }
          >
            {isGenerating ? (
              <>
                <RefreshCw size={17} className="sim-spinning" />
                Generating telemetry...
              </>
            ) : (
              <>
                <Play size={17} fill="currentColor" />
                Generate synthetic telemetry
              </>
            )}
          </button>

          <p className="sim-form-footnote">
            Generation writes synthetic readings and any resulting
            explainable alerts to the demo database.
          </p>
        </form>

        <aside className="sim-context-card">
          <div className="sim-context-icon">
            <Waves size={23} />
          </div>

          <span className="sim-section-label">ACTIVE CONFIGURATION</span>
          <h3>{selectedScenario?.name}</h3>
          <p>{selectedScenario?.description}</p>

          <div className="sim-context-divider" />

          <div className="sim-context-item">
            <Users size={16} />
            <div>
              <span>Selected astronaut</span>
              <strong>
                {selectedAstronaut
                  ? getAstronautName(selectedAstronaut)
                  : "Not selected"}
              </strong>
            </div>
          </div>

          <div className="sim-context-item">
            <Clock3 size={16} />
            <div>
              <span>Sampling configuration</span>
              <strong>{count} readings Â· {intervalSeconds}s interval</strong>
            </div>
          </div>

          <div className="sim-context-item">
            <Zap size={16} />
            <div>
              <span>Data classification</span>
              <strong>{selectedScenario?.quality || "--"}</strong>
            </div>
          </div>

          {scenario === "DATA_QUALITY_FAULT" && (
            <div className="sim-quality-warning">
              <AlertTriangle size={16} />
              Placeholder values in UNGRADABLE records must not
              be interpreted as health measurements.
            </div>
          )}
        </aside>
      </section>

      {result && (
        <section className="sim-results-section">
          <div className="sim-section-heading">
            <div>
              <span className="sim-section-label">03 / GENERATION REPORT</span>
              <h2>Simulation results</h2>
            </div>
            <span className="sim-result-status">
              <CheckCircle2 size={15} /> GENERATION COMPLETE
            </span>
          </div>

          <div className="sim-result-grid">
            <div className="sim-result-card">
              <Activity size={19} />
              <span>Generated readings</span>
              <strong>{displayValue(summary.total_readings ?? readings.length)}</strong>
            </div>

            <div className="sim-result-card">
              <ShieldAlert size={19} />
              <span>Alerts created</span>
              <strong>
                {displayValue(
                  alertGeneration.created ??
                  alertGeneration.created_count ??
                  alertGeneration.alerts_created ??
                  "--"
                )}
              </strong>
            </div>

            <div className="sim-result-card">
              <Radio size={19} />
              <span>Scenario</span>
              <strong className="sim-result-scenario">
                {result.scenario || scenario}
              </strong>
            </div>

            <div className="sim-result-card">
              <Clock3 size={19} />
              <span>Last recorded</span>
              <strong className="sim-result-date">
                {formatDate(summary.last_recorded_at)}
              </strong>
            </div>
          </div>

          <div className="sim-results-panel">
            <div className="sim-results-panel-heading">
              <div>
                <h3>Generated telemetry</h3>
                <p>
                  {result.astronaut?.full_name || "Synthetic astronaut"}
                  {" Â· "}
                  {result.astronaut?.astronaut_code || "--"}
                </p>
              </div>
              <span className="sim-result-count">
                {readings.length} RECORDS
              </span>
            </div>

            {readings.length === 0 ? (
              <div className="sim-empty-state">
                No reading details were returned by the API.
              </div>
            ) : (
              <div className="sim-table-scroll">
                <table className="sim-readings-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Heart rate</th>
                      <th>SpOâ‚‚</th>
                      <th>Temperature</th>
                      <th>Resp. rate</th>
                      <th>Quality</th>
                      <th>Recorded at</th>
                    </tr>
                  </thead>
                  <tbody>
                    {readings.map((reading) => (
                      <tr key={reading.id}>
                        <td>#{reading.id}</td>
                        <td>{displayValue(reading.heart_rate_bpm)} BPM</td>
                        <td>{displayValue(reading.spo2_percent)}%</td>
                        <td>{displayValue(reading.body_temperature_c)} Â°C</td>
                        <td>{displayValue(reading.respiratory_rate_bpm)}</td>
                        <td>
                          <span
                            className={`sim-quality-badge sim-quality-${String(
                              reading.data_quality || "unknown"
                            ).toLowerCase()}`}
                          >
                            {displayValue(reading.data_quality)}
                          </span>
                        </td>
                        <td>{formatDate(reading.recorded_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="sim-results-panel">
            <div className="sim-results-panel-heading">
              <div>
                <h3>Alert generation report</h3>
                <p>Persistent alert creation summary returned by backend</p>
              </div>
            </div>

            <div className="sim-alert-report">
              {Object.entries(alertGeneration).length === 0 ? (
                <span>No alert-generation summary returned.</span>
              ) : (
                Object.entries(alertGeneration).map(([key, value]) => (
                  <div className="sim-alert-report-item" key={key}>
                    <span>{key.replaceAll("_", " ")}</span>
                    <strong>
                      {typeof value === "object"
                        ? JSON.stringify(value)
                        : displayValue(value)}
                    </strong>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="sim-result-disclaimer">
            <AlertTriangle size={16} />
            {result.disclaimer ||
              "Synthetic demonstration data only. Not for clinical or operational use."}
          </div>
        </section>
      )}
      <HabitatSimulatorPanel missions={missions} />

      <MissionDigitalTwinPanel missions={missions} />

    </div>
  );
}

export default SimulatorPage;
