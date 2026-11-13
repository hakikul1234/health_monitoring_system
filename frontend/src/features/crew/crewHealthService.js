import api from "../../lib/api";

function normalizeList(responseData) {
  if (Array.isArray(responseData)) {
    return responseData;
  }

  if (Array.isArray(responseData?.results)) {
    return responseData.results;
  }

  if (responseData?.success === true &&
      Array.isArray(responseData.data)) {
    return responseData.data;
  }

  throw new Error("Invalid list response received from the API.");
}

export async function getAstronauts() {
  const response = await api.get("/crew/astronauts/");
  return normalizeList(response.data);
}

export async function getHealthReadings() {
  const response = await api.get("/health/readings/");
  return normalizeList(response.data);
}

export async function getAstronautById(id) {
  if (!id) {
    throw new Error("Astronaut ID is required.");
  }

  const response = await api.get(`/crew/astronauts/${id}/`);
  return response.data;
}

export async function getHealthReadingAnalysis(readingId) {
  if (!readingId) {
    throw new Error("Reading ID is required.");
  }

  const response = await api.get(
    `/health/readings/${readingId}/analysis/`
  );

  return response.data;
}
