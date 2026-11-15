import api from "../../lib/api";

function normalizeList(responseData, resourceName, collectionKey) {
  if (Array.isArray(responseData)) {
    return responseData;
  }

  if (Array.isArray(responseData?.[collectionKey])) {
    return responseData[collectionKey];
  }

  if (Array.isArray(responseData?.results)) {
    return responseData.results;
  }

  if (
    responseData?.success === true &&
    Array.isArray(responseData.data)
  ) {
    return responseData.data;
  }

  throw new Error(
    `Invalid ${resourceName} list response received from API.`
  );
}

export async function getSimulatorAstronauts() {
  const response = await api.get("/crew/astronauts/");
  return normalizeList(response.data, "astronauts");
}

export async function getSimulatorMissions() {
  const response = await api.get("/missions/");
  return normalizeList(response.data, "missions");
}

export async function generateTelemetry(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Valid simulator configuration is required.");
  }

  const response = await api.post(
    "/simulator/telemetry/generate/",
    payload
  );

  return response.data;
}

// Virtual Health Sensor API
export async function getVirtualHealthSensors() {
  const response = await api.get("/simulator/sensors/");
  return normalizeList(response.data, "virtual sensors", "sensors");
}

export async function registerVirtualHealthSensor(payload) {
  if (!payload || typeof payload !== "object") {
    throw new Error("Valid sensor registration details are required.");
  }

  const response = await api.post("/simulator/sensors/", payload);
  return response.data;
}

export async function simulateVirtualSensor(sensorId, payload) {
  if (!sensorId) {
    throw new Error("Select a virtual sensor before simulation.");
  }

  if (!payload || typeof payload !== "object") {
    throw new Error("Valid simulation configuration is required.");
  }

  const response = await api.post(
    `/simulator/sensors/${encodeURIComponent(sensorId)}/simulate/`,
    payload
  );

  return response.data;
}

export async function getVirtualSensorRuns() {
  const response = await api.get("/simulator/sensor-runs/");
  return normalizeList(response.data, "sensor simulation runs", "runs");
}

// Trust-Aware Decision Engine API
export async function evaluateReadingTrust(payload) {
  if (!payload || !Number.isInteger(Number(payload.reading_id)) || Number(payload.reading_id) < 1) {
    throw new Error("A valid database reading ID is required.");
  }

  const requestPayload = {
    reading_id: Number(payload.reading_id),
  };

  if (payload.cross_check_reading_id !== undefined &&
      payload.cross_check_reading_id !== null &&
      payload.cross_check_reading_id !== "") {
    const crossCheckId = Number(payload.cross_check_reading_id);

    if (!Number.isInteger(crossCheckId) || crossCheckId < 1) {
      throw new Error("A valid independent reading ID is required.");
    }

    if (crossCheckId === requestPayload.reading_id) {
      throw new Error("The independent reading must have a different ID.");
    }

    requestPayload.cross_check_reading_id = crossCheckId;
  }

  const response = await api.post(
    "/simulator/trust-decisions/",
    requestPayload
  );

  return response.data;
}

