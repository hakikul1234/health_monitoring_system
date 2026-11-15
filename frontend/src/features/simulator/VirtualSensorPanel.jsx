import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  Cpu,
  History,
  Radio,
  RefreshCw,
  ShieldCheck,
  Signal,
  WifiOff,
  Zap,
} from "lucide-react";

import useSimulatorStore from "./simulatorStore";
import VirtualSensorBody from "./VirtualSensorBody";
import "./VirtualSensorPanel.css";

const SCENARIOS = [
  { value: "NORMAL_MISSION", label: "Normal Mission" },
  { value: "HEALTH_ANOMALY", label: "Health Anomaly" },
  { value: "EMERGENCY_MISSION", label: "Emergency Mission" },
  { value: "DATA_QUALITY_FAULT", label: "Data Quality Fault" },
];

const FAULT_MODES = [
  { value: "NORMAL", label: "Normal Operation", description: "No injected sensor fault." },
  { value: "NOISE", label: "Signal Noise", description: "Adds synthetic measurement noise." },
  { value: "DROPOUT", label: "Packet Dropout", description: "Simulates missing sensor packets." },
  { value: "DRIFT", label: "Sensor Drift", description: "Simulates gradual measurement drift." },
  { value: "DISCONNECTED", label: "Disconnected", description: "Simulates a disconnected sensor." },
];

function astronautName(astronaut) {
  return (
    astronaut?.profile?.full_name ||
    astronaut?.full_name ||
    astronaut?.call_sign ||
    astronaut?.astronaut_code ||
    `Astronaut #${astronaut?.id}`
  );
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? "—"
    : date.toLocaleString();
}

function QualityBadge({ quality }) {
  const normalized = String(quality || "UNKNOWN").toUpperCase();

  return (
    <span className={`vs-quality vs-quality-${normalized.toLowerCase()}`}>
      {normalized}
    </span>
  );
}

function VirtualSensorPanel() {
  const astronauts = useSimulatorStore((state) => state.astronauts);
  const missions = useSimulatorStore((state) => state.missions);

  const sensors = useSimulatorStore((state) => state.virtualSensors);
  const runs = useSimulatorStore((state) => state.sensorRuns);
  const result = useSimulatorStore((state) => state.sensorResult);

  const isLoading = useSimulatorStore((state) => state.isLoadingSensors);
  const isRegistering = useSimulatorStore((state) => state.isRegisteringSensor);
  const isRunning = useSimulatorStore((state) => state.isRunningSensor);
  const error = useSimulatorStore((state) => state.sensorError);

  const fetchVirtualSensors = useSimulatorStore((state) => state.fetchVirtualSensors);
  const registerSensor = useSimulatorStore((state) => state.registerSensor);
  const runSimulation = useSimulatorStore((state) => state.runVirtualSensorSimulation);
  const clearResult = useSimulatorStore((state) => state.clearSensorResult);

  const trustDecision = useSimulatorStore((state) => state.trustDecision);
  const isEvaluatingTrust = useSimulatorStore((state) => state.isEvaluatingTrust);
  const trustDecisionError = useSimulatorStore((state) => state.trustDecisionError);
  const evaluateTrust = useSimulatorStore((state) => state.evaluateReadingTrust);
  const clearTrustDecision = useSimulatorStore((state) => state.clearTrustDecision);

  const [selectedSensorId, setSelectedSensorId] = useState("");
  const [crossCheckReadingId, setCrossCheckReadingId] = useState("");

  const [sensorForm, setSensorForm] = useState({
    sensor_code: "",
    astronaut_id: "",
    mission_id: "",
    manufacturer: "",
    model_number: "",
    firmware_version: "",
  });

  const [simulationForm, setSimulationForm] = useState({
    scenario: "NORMAL_MISSION",
    fault_mode: "NORMAL",
    count: 10,
    interval_seconds: 60,
    seed: "",
    noise_level_percent: 5,
    packet_loss_percent: 10,
  });

  const [registrationMessage, setRegistrationMessage] = useState("");
  const [actionError, setActionError] = useState("");

  useEffect(() => {
    fetchVirtualSensors().catch(() => {});
  }, [fetchVirtualSensors]);

  const selectedSensor = useMemo(
    () => sensors.find((sensor) => String(sensor.id) === String(selectedSensorId)),
    [sensors, selectedSensorId]
  );

  const availableMissions = useMemo(() => {
    if (!sensorForm.astronaut_id) return missions;

    return missions.filter((mission) => {
      const crew = mission?.crew || [];

      return crew.some(
        (member) =>
          String(member?.id ?? member) === String(sensorForm.astronaut_id)
      );
    });
  }, [missions, sensorForm.astronaut_id]);

  const readings = result?.readings || [];
  const summary = result?.summary || {};
  const qualityCounts = summary?.quality_counts || {};

  const updateSensorField = (event) => {
    const { name, value } = event.target;

    setSensorForm((previous) => ({
      ...previous,
      [name]: value,
      ...(name === "astronaut_id" ? { mission_id: "" } : {}),
    }));
  };

  const updateSimulationField = (event) => {
    const { name, value } = event.target;

    setSimulationForm((previous) => ({
      ...previous,
      [name]: value,
    }));

    clearResult();
    clearTrustDecision();
    setActionError("");
  };

  const handleRegistration = async (event) => {
    event.preventDefault();

    setActionError("");
    setRegistrationMessage("");

    if (!sensorForm.sensor_code.trim()) {
      setActionError("Sensor code is required.");
      return;
    }

    if (!sensorForm.astronaut_id) {
      setActionError("Select an astronaut before registering a sensor.");
      return;
    }

    const payload = {
      sensor_code: sensorForm.sensor_code.trim(),
      astronaut_id: Number(sensorForm.astronaut_id),
      mission_id: sensorForm.mission_id
        ? Number(sensorForm.mission_id)
        : null,
      manufacturer: sensorForm.manufacturer.trim(),
      model_number: sensorForm.model_number.trim(),
      firmware_version: sensorForm.firmware_version.trim(),
    };

    try {
      const response = await registerSensor(payload);
      const registeredSensor = response?.sensor;

      if (registeredSensor?.id) {
        setSelectedSensorId(String(registeredSensor.id));
      }

      setSensorForm({
        sensor_code: "",
        astronaut_id: "",
        mission_id: "",
        manufacturer: "",
        model_number: "",
        firmware_version: "",
      });

      setRegistrationMessage("Virtual sensor registered successfully.");
    } catch (requestError) {
      setActionError(
        requestError?.response?.data?.message ||
        requestError?.message ||
        "Sensor registration failed."
      );
    }
  };

  const handleSimulation = async (event) => {
    event.preventDefault();

    setActionError("");
    clearResult();
    clearTrustDecision();

    if (!selectedSensorId) {
      setActionError("Select a virtual sensor before starting simulation.");
      return;
    }

    const faultMode = simulationForm.fault_mode;

    const payload = {
      scenario: simulationForm.scenario,
      fault_mode: faultMode,
      count: Number(simulationForm.count),
      interval_seconds: Number(simulationForm.interval_seconds),
      seed: simulationForm.seed.trim()
        ? Number(simulationForm.seed)
        : null,
      noise_level_percent:
        faultMode === "NOISE"
          ? Number(simulationForm.noise_level_percent)
          : 0,
      packet_loss_percent:
        faultMode === "DROPOUT"
          ? Number(simulationForm.packet_loss_percent)
          : 0,
    };

    if (
      !Number.isInteger(payload.count) ||
      payload.count < 1 ||
      payload.count > 1000
    ) {
      setActionError("Sample count must be between 1 and 1000.");
      return;
    }

    if (
      !Number.isInteger(payload.interval_seconds) ||
      payload.interval_seconds < 1 ||
      payload.interval_seconds > 3600
    ) {
      setActionError("Interval must be between 1 and 3600 seconds.");
      return;
    }

    if (payload.seed !== null && !Number.isSafeInteger(payload.seed)) {
      setActionError("Seed must be a valid safe integer.");
      return;
    }

    if (faultMode === "NOISE" && payload.noise_level_percent <= 0) {
      setActionError("Noise level must be greater than zero.");
      return;
    }

    if (faultMode === "DROPOUT" && payload.packet_loss_percent <= 0) {
      setActionError("Packet loss must be greater than zero.");
      return;
    }

    try {
      await runSimulation(selectedSensorId, payload);
    } catch (requestError) {
      setActionError(
        requestError?.response?.data?.message ||
        requestError?.message ||
        "Virtual sensor simulation failed."
      );
    }
  };

  const handleTrustEvaluation = async (readingId) => {
    if (!Number.isInteger(Number(readingId)) || Number(readingId) < 1) {
      return;
    }

    const candidateId = crossCheckReadingId.trim()
      ? Number(crossCheckReadingId)
      : null;

    if (
      candidateId !== null &&
      (!Number.isInteger(candidateId) || candidateId < 1)
    ) {
      return;
    }

    if (candidateId !== null && candidateId === Number(readingId)) {
      return;
    }

    try {
      await evaluateTrust({
        reading_id: Number(readingId),
        ...(candidateId !== null
          ? { cross_check_reading_id: candidateId }
          : {}),
      });
    } catch {
      // The Zustand store exposes the API error in trustDecisionError.
    }
  };

  const decisionPayload = trustDecision?.trust_decision || null;
  const decisionName = String(decisionPayload?.decision || "").toUpperCase();
  const decisionClass = decisionName.toLowerCase().replaceAll("_", "-");

  const selectedFault = FAULT_MODES.find(
    (mode) => mode.value === simulationForm.fault_mode
  );

  return (
    <section className="vs-panel" aria-labelledby="vs-heading">
      <div className="vs-heading">
        <div>
          <span className="vs-eyebrow">
            <span className="vs-live-dot" />
            SYNTHETIC SENSOR INFRASTRUCTURE
          </span>

          <h2 id="vs-heading">Virtual Sensor Simulation Engine</h2>

          <p>
            Register software-defined crew sensors, inject controlled faults,
            and inspect synthetic telemetry quality.
          </p>
        </div>

        <div className="vs-heading-icon">
          <Radio size={25} />
        </div>
      </div>

      <div className="vs-disclaimer">
        <ShieldCheck size={17} />
        <span>
          Software simulation only. No physical sensor is connected.
          Generated values are synthetic demonstrations, not clinical
          measurements or validated spacecraft safety limits.
        </span>
      </div>

      {(error || actionError) && (
        <div className="vs-message vs-message-error" role="alert">
          <AlertTriangle size={17} />
          <span>{actionError || error}</span>
        </div>
      )}

      {registrationMessage && (
        <div className="vs-message vs-message-success" role="status">
          <CheckCircle2 size={17} />
          <span>{registrationMessage}</span>
        </div>
      )}

      <div className="vs-section-heading">
        <div>
          <span className="vs-step">01</span>
          <h3>Sensor Registry</h3>
        </div>

        <span className="vs-count">
          {sensors.length} registered
        </span>
      </div>

      <div className="vs-registry-grid">
        <form className="vs-card vs-registration-form" onSubmit={handleRegistration}>
          <div className="vs-card-heading">
            <Cpu size={19} />
            <h4>Register Virtual Sensor</h4>
          </div>

          <label className="vs-field">
            Sensor Code *
            <input
              name="sensor_code"
              value={sensorForm.sensor_code}
              onChange={updateSensorField}
              placeholder="VHS-ALPHA-001"
              maxLength={64}
              required
            />
          </label>

          <label className="vs-field">
            Assigned Astronaut *
            <span className="vs-select-wrap">
              <select
                name="astronaut_id"
                value={sensorForm.astronaut_id}
                onChange={updateSensorField}
                required
              >
                <option value="">Select astronaut</option>
                {astronauts.map((astronaut) => (
                  <option key={astronaut.id} value={astronaut.id}>
                    {astronautName(astronaut)}
                  </option>
                ))}
              </select>
              <ChevronDown size={15} />
            </span>
          </label>

          <label className="vs-field">
            Assigned Mission
            <span className="vs-select-wrap">
              <select
                name="mission_id"
                value={sensorForm.mission_id}
                onChange={updateSensorField}
                disabled={!sensorForm.astronaut_id}
              >
                <option value="">No mission assignment</option>
                {availableMissions.map((mission) => (
                  <option key={mission.id} value={mission.id}>
                    {mission.name || mission.mission_code || `Mission #${mission.id}`}
                  </option>
                ))}
              </select>
              <ChevronDown size={15} />
            </span>
          </label>

          <div className="vs-two-columns">
            <label className="vs-field">
              Manufacturer
              <input
                name="manufacturer"
                value={sensorForm.manufacturer}
                onChange={updateSensorField}
                placeholder="Demo manufacturer"
              />
            </label>

            <label className="vs-field">
              Model Number
              <input
                name="model_number"
                value={sensorForm.model_number}
                onChange={updateSensorField}
                placeholder="MODEL-X"
              />
            </label>
          </div>

          <label className="vs-field">
            Firmware Version
            <input
              name="firmware_version"
              value={sensorForm.firmware_version}
              onChange={updateSensorField}
              placeholder="1.0.0"
            />
          </label>

          <button
            type="submit"
            className="vs-primary-button"
            disabled={isRegistering || astronauts.length === 0}
          >
            {isRegistering ? (
              <RefreshCw className="vs-spin" size={16} />
            ) : (
              <Radio size={16} />
            )}
            {isRegistering ? "Registering..." : "Register Sensor"}
          </button>

          {astronauts.length === 0 && (
            <p className="vs-help">
              Astronaut options are not available yet. Check simulator options.
            </p>
          )}
        </form>

        <div className="vs-card vs-sensor-list">
          <div className="vs-card-heading">
            <Signal size={19} />
            <h4>Registered Sensors</h4>

            <button
              type="button"
              className="vs-icon-button"
              onClick={() => fetchVirtualSensors().catch(() => {})}
              disabled={isLoading}
              aria-label="Refresh sensors"
              title="Refresh sensors"
            >
              <RefreshCw size={15} className={isLoading ? "vs-spin" : ""} />
            </button>
          </div>

          {isLoading ? (
            <div className="vs-empty">
              <RefreshCw className="vs-spin" size={21} />
              <span>Loading sensor registry...</span>
            </div>
          ) : sensors.length === 0 ? (
            <div className="vs-empty">
              <Radio size={25} />
              <strong>No virtual sensors registered</strong>
              <span>Register a sensor to begin simulation.</span>
            </div>
          ) : (
            <div className="vs-sensor-items">
              {sensors.map((sensor) => {
                const active =
                  String(sensor.id) === String(selectedSensorId);

                return (
                  <button
                    type="button"
                    key={sensor.id}
                    className={`vs-sensor-item ${active ? "vs-sensor-selected" : ""}`}
                    onClick={() => {
                      setSelectedSensorId(String(sensor.id));
                      clearResult();
                      clearTrustDecision();
                      setCrossCheckReadingId("");
                      setActionError("");
                    }}
                  >
                    <span className="vs-sensor-symbol">
                      <Activity size={18} />
                    </span>

                    <span className="vs-sensor-info">
                      <strong>{sensor.sensor_code}</strong>
                      <small>
                        Astronaut #{sensor.astronaut_id}
                        {sensor.mission_id ? ` · Mission #${sensor.mission_id}` : ""}
                      </small>
                    </span>

                    <span className={`vs-status vs-status-${String(sensor.status || "ACTIVE").toLowerCase()}`}>
                      {sensor.status || "UNKNOWN"}
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          {selectedSensor && (
            <div className="vs-selected-detail">
              <span>SELECTED SENSOR</span>
              <strong>{selectedSensor.sensor_code}</strong>
              <small>
                {selectedSensor.manufacturer || "Manufacturer unspecified"}
                {selectedSensor.model_number
                  ? ` · ${selectedSensor.model_number}`
                  : ""}
              </small>
            </div>
          )}
        </div>
      </div>

      <VirtualSensorBody selectedSensor={selectedSensor} />

      <div className="vs-section-heading">
        <div>
          <span className="vs-step">02</span>
          <h3>Simulation Configuration</h3>
        </div>
      </div>

      <form className="vs-card vs-simulation-form" onSubmit={handleSimulation}>
        <div className="vs-card-heading">
          <Zap size={19} />
          <h4>Configure Synthetic Telemetry</h4>
        </div>

        <div className="vs-form-grid">
          <label className="vs-field">
            Mission Scenario
            <span className="vs-select-wrap">
              <select
                name="scenario"
                value={simulationForm.scenario}
                onChange={updateSimulationField}
              >
                {SCENARIOS.map((scenario) => (
                  <option key={scenario.value} value={scenario.value}>
                    {scenario.label}
                  </option>
                ))}
              </select>
              <ChevronDown size={15} />
            </span>
          </label>

          <label className="vs-field">
            Sensor Fault Mode
            <span className="vs-select-wrap">
              <select
                name="fault_mode"
                value={simulationForm.fault_mode}
                onChange={updateSimulationField}
              >
                {FAULT_MODES.map((mode) => (
                  <option key={mode.value} value={mode.value}>
                    {mode.label}
                  </option>
                ))}
              </select>
              <ChevronDown size={15} />
            </span>
          </label>

          <label className="vs-field">
            Sample Count
            <input
              type="number"
              name="count"
              min="1"
              max="1000"
              value={simulationForm.count}
              onChange={updateSimulationField}
              required
            />
          </label>

          <label className="vs-field">
            Interval (seconds)
            <input
              type="number"
              name="interval_seconds"
              min="1"
              max="3600"
              value={simulationForm.interval_seconds}
              onChange={updateSimulationField}
              required
            />
          </label>

          {simulationForm.fault_mode === "NOISE" && (
            <label className="vs-field">
              Noise Level (%)
              <input
                type="number"
                name="noise_level_percent"
                min="0.01"
                max="100"
                step="0.01"
                value={simulationForm.noise_level_percent}
                onChange={updateSimulationField}
                required
              />
            </label>
          )}

          {simulationForm.fault_mode === "DROPOUT" && (
            <label className="vs-field">
              Packet Loss (%)
              <input
                type="number"
                name="packet_loss_percent"
                min="0.01"
                max="100"
                step="0.01"
                value={simulationForm.packet_loss_percent}
                onChange={updateSimulationField}
                required
              />
            </label>
          )}

          <label className="vs-field">
            Random Seed
            <input
              type="number"
              name="seed"
              value={simulationForm.seed}
              onChange={updateSimulationField}
              placeholder="Optional reproducibility seed"
            />
          </label>
        </div>

        {selectedFault && (
          <div className="vs-fault-description">
            {simulationForm.fault_mode === "DISCONNECTED" ? (
              <WifiOff size={17} />
            ) : (
              <Activity size={17} />
            )}
            <span>
              <strong>{selectedFault.label}:</strong> {selectedFault.description}
            </span>
          </div>
        )}

        <div className="vs-simulation-actions">
          <span className="vs-selection-hint">
            {selectedSensor
              ? `Target: ${selectedSensor.sensor_code}`
              : "Select a registered sensor first"}
          </span>

          <button
            type="submit"
            className="vs-primary-button"
            disabled={isRunning || !selectedSensorId}
          >
            {isRunning ? (
              <RefreshCw className="vs-spin" size={16} />
            ) : (
              <Zap size={16} />
            )}
            {isRunning ? "Simulating..." : "Run Sensor Simulation"}
          </button>
        </div>
      </form>

      {result && (
        <>
          <div className="vs-section-heading">
            <div>
              <span className="vs-step">03</span>
              <h3>Simulation Results</h3>
            </div>

            <span className={`vs-status vs-status-${String(summary.run_status || "completed").toLowerCase()}`}>
              {summary.run_status || "COMPLETED"}
            </span>
          </div>

          <div className="vs-result-grid">
            <div className="vs-result-card">
              <span>Requested Samples</span>
              <strong>{summary.requested_count ?? readings.length}</strong>
            </div>

            <div className="vs-result-card">
              <span>Generated Samples</span>
              <strong>{summary.generated_count ?? readings.length}</strong>
            </div>

            <div className="vs-result-card">
              <span>Dropped Packets</span>
              <strong>{summary.dropped_packets ?? 0}</strong>
            </div>

            <div className="vs-result-card">
              <span>Fault Mode</span>
              <strong className="vs-result-mode">{summary.fault_mode || "NORMAL"}</strong>
            </div>
          </div>

          <div className="vs-card vs-trust-card">
            <div className="vs-card-heading">
              <ShieldCheck size={19} />
              <h4>Trust-Aware Decision Engine</h4>
              <span className="vs-count">Engine {decisionPayload?.engine_version || "1.1.0"}</span>
            </div>

            <p className="vs-help">
              Evaluate whether a synthetic reading is suitable for software
              decision support. This is a sensor/data trust assessment, not a
              medical diagnosis or flight-safety certification.
            </p>

            <label className="vs-field vs-cross-check-field">
              Independent sensor reading database ID (optional)
              <input
                type="number"
                min="1"
                step="1"
                value={crossCheckReadingId}
                onChange={(event) => {
                  setCrossCheckReadingId(event.target.value);
                  clearTrustDecision();
                }}
                placeholder="Enter another reading ID"
              />
            </label>

            <p className="vs-help">
              Only provide an ID belonging to a different sensor assigned to
              the same astronaut. The backend verifies whether it is eligible.
              Readings from this current sensor run are not independent.
            </p>

            {trustDecisionError && (
              <div className="vs-message vs-message-error" role="alert">
                <AlertTriangle size={17} />
                <span>{trustDecisionError}</span>
              </div>
            )}

            {decisionPayload ? (
              <div className="vs-trust-result">
                <div className="vs-trust-result-heading">
                  <span className="vs-trust-label">ENGINE DECISION</span>
                  <span className={`vs-trust-decision vs-trust-${decisionClass}`}>
                    {decisionName.replaceAll("_", " ")}
                  </span>
                </div>

                <div className="vs-trust-detail">
                  <strong>Reason</strong>
                  <span>{decisionPayload.reason_code || "Not supplied"}</span>
                </div>

                <div className="vs-trust-detail">
                  <strong>Explanation</strong>
                  <span>{decisionPayload.explanation || "No explanation supplied."}</span>
                </div>

                <div className="vs-trust-detail">
                  <strong>Recommended next action</strong>
                  <span>{decisionPayload.next_action || "No next action supplied."}</span>
                </div>

                {decisionPayload.evidence && (
                  <details className="vs-trust-evidence">
                    <summary>View decision evidence</summary>
                    <pre>{JSON.stringify(decisionPayload.evidence, null, 2)}</pre>
                  </details>
                )}

                {decisionName === "CROSS_CHECK" && (
                  <p className="vs-help">
                    Independent evidence was found. No measurement comparison
                    was performed by this decision.
                  </p>
                )}

                <small>
                  {decisionPayload.medical_disclaimer ||
                    "Synthetic software decision support only. Not for clinical or flight use."}
                </small>
              </div>
            ) : (
              <div className="vs-empty vs-trust-empty">
                <ShieldCheck size={23} />
                <strong>
                  {isEvaluatingTrust ? "Evaluating reading trust..." : "No trust decision yet"}
                </strong>
                <span>
                  Select Evaluate Trust on a generated reading below.
                </span>
                {isEvaluatingTrust && <RefreshCw className="vs-spin" size={17} />}
              </div>
            )}
          </div>

          <div className="vs-card vs-quality-card">
            <div className="vs-card-heading">
              <Activity size={19} />
              <h4>Data Quality Distribution</h4>
            </div>

            <div className="vs-quality-grid">
              {["VALID", "SUSPECT", "UNGRADABLE"].map((quality) => (
                <div className="vs-quality-stat" key={quality}>
                  <QualityBadge quality={quality} />
                  <strong>{qualityCounts[quality] ?? 0}</strong>
                  <small>Readings</small>
                </div>
              ))}
            </div>

            <p className="vs-help">
              UNGRADABLE readings are counted for quality reporting only.
              Their measurement values must not be interpreted.
            </p>
          </div>

          <div className="vs-card vs-alert-card">
            <div className="vs-card-heading">
              <ShieldCheck size={19} />
              <h4>Alert Processing Summary</h4>
            </div>

            <p>
              {result.alert_generation?.message ||
                result.alert_generation?.status ||
                "No additional alert-processing message supplied."}
            </p>

            <small>
              Sensor fault observations are separate from crew-health
              alerts. Noise and drift modes suppress medical-style alert
              generation in this simulation.
            </small>
          </div>

          <div className="vs-card vs-readings-card">
            <div className="vs-card-heading">
              <Activity size={19} />
              <h4>Generated Reading Records</h4>
              <span className="vs-count">{readings.length} records</span>
            </div>

            {readings.length === 0 ? (
              <div className="vs-empty">
                <WifiOff size={23} />
                <strong>No readings generated</strong>
                <span>
                  The selected simulation mode may represent a disconnected sensor.
                </span>
              </div>
            ) : (
              <div className="vs-table-scroll">
                <table className="vs-table">
                  <thead>
                    <tr>
                      <th>Record</th>
                      <th>Heart Rate</th>
                      <th>SpO₂</th>
                      <th>Temperature</th>
                      <th>Respiratory Rate</th>
                      <th>Quality</th>
                      <th>Trust Action</th>
                    </tr>
                  </thead>

                  <tbody>
                    {readings.map((reading) => {
                      const ungradable =
                        String(reading.data_quality).toUpperCase() === "UNGRADABLE";

                      return (
                        <tr key={reading.id || reading.sample_id}>
                          <td>
                            {reading.sample_id || `#${reading.id}`}
                          </td>

                          <td>{ungradable ? "—" : `${reading.heart_rate_bpm ?? "—"} bpm`}</td>
                          <td>{ungradable ? "—" : `${reading.spo2_percent ?? "—"}%`}</td>
                          <td>{ungradable ? "—" : `${reading.body_temperature_c ?? "—"} °C`}</td>
                          <td>{ungradable ? "—" : `${reading.respiratory_rate_bpm ?? "—"} /min`}</td>

                          <td>
                            <QualityBadge quality={reading.data_quality} />
                          </td>

                          <td>
                            <button
                              type="button"
                              className="vs-trust-button"
                              onClick={() => handleTrustEvaluation(reading.id)}
                              disabled={!reading.id || isEvaluatingTrust}
                              title={
                                reading.id
                                  ? `Evaluate database reading #${reading.id}`
                                  : "Database reading ID unavailable"
                              }
                            >
                              {isEvaluatingTrust ? (
                                <RefreshCw size={14} className="vs-spin" />
                              ) : (
                                <ShieldCheck size={14} />
                              )}
                              Evaluate Trust
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            <p className="vs-help">
              Every record shown here is synthetic software-generated telemetry.
              Values are not clinical observations.
            </p>
          </div>
        </>
      )}

      <div className="vs-section-heading">
        <div>
          <span className="vs-step">04</span>
          <h3>Simulation Run History</h3>
        </div>

        <span className="vs-count">
          Latest {runs.length} runs
        </span>
      </div>

      <div className="vs-card vs-history-card">
        <div className="vs-card-heading">
          <History size={19} />
          <h4>Recent Sensor Runs</h4>
        </div>

        {runs.length === 0 ? (
          <div className="vs-empty">
            <History size={23} />
            <strong>No simulation history available</strong>
            <span>Completed sensor runs will appear here.</span>
          </div>
        ) : (
          <div className="vs-history-list">
            {runs.map((run) => (
              <div className="vs-history-item" key={run.id}>
                <span className="vs-history-icon">
                  <Activity size={17} />
                </span>

                <div className="vs-history-info">
                  <strong>{run.sensor_code || `Sensor #${run.sensor}`}</strong>
                  <span>
                    {run.fault_mode} · {run.generated_count}/{run.requested_count} samples
                  </span>
                  <small>{formatDate(run.started_at)}</small>
                </div>

                <span className={`vs-status vs-status-${String(run.status || "completed").toLowerCase()}`}>
                  {run.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

export default VirtualSensorPanel;
