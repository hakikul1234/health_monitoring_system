import api from "../../lib/api";

function normalizeList(responseData) {
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

  throw new Error("Invalid missions list response received from API.");
}

export async function getMissions() {
  const response = await api.get("/missions/");
  return normalizeList(response.data);
}

export async function getMissionById(id) {
  if (!id) {
    throw new Error("Mission ID is required.");
  }

  const response = await api.get(`/missions/${id}/`);
  return response.data;
}

export async function createMission(missionData) {
  if (!missionData || typeof missionData !== "object") {
    throw new Error("Valid mission data is required.");
  }

  const response = await api.post("/missions/", missionData);
  return response.data;
}

export async function updateMission(id, missionData) {
  if (!id) {
    throw new Error("Mission ID is required for updating.");
  }

  const response = await api.patch(
    `/missions/${id}/`,
    missionData
  );

  return response.data;
}

export async function deleteMission(id) {
  if (!id) {
    throw new Error("Mission ID is required for deletion.");
  }

  await api.delete(`/missions/${id}/`);

  return id;
}
