import api from "../../lib/api";

function normalizeList(responseData, resourceName) {
  if (Array.isArray(responseData)) {
    return responseData;
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