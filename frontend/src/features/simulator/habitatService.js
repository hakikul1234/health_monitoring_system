import api from "../../lib/api";

export const HABITAT_SCENARIOS = [
  {
    id: "NORMAL_HABITAT",
    name: "Normal Habitat",
    description: "Baseline synthetic cabin environment.",
    tone: "normal",
  },
  {
    id: "ELEVATED_CO2",
    name: "Elevated CO2",
    description: "Illustrative increase in cabin carbon dioxide.",
    tone: "warning",
  },
  {
    id: "PRESSURE_DEVIATION",
    name: "Pressure Deviation",
    description: "Synthetic cabin pressure deviation scenario.",
    tone: "critical",
  },
  {
    id: "TEMPERATURE_HUMIDITY_ANOMALY",
    name: "Temperature & Humidity",
    description: "Illustrative temperature and humidity anomaly.",
    tone: "warning",
  },
  {
    id: "SENSOR_QUALITY_FAULT",
    name: "Sensor Quality Fault",
    description: "Ungradable sensor data with unusable placeholders.",
    tone: "fault",
  },
];

export async function generateHabitatTelemetry(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Valid habitat simulation configuration is required.");
  }

  const response = await api.post(
    "/simulator/habitat/generate/",
    payload
  );

  const data = response.data;

  if (
    !data ||
    data.success !== true ||
    !Array.isArray(data.readings) ||
    !data.summary
  ) {
    throw new Error("Invalid habitat telemetry response received from API.");
  }

  return data;
}
