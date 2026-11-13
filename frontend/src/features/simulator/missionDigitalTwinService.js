import api from "../../lib/api";

export async function getMissionDigitalTwinSummary(missionId) {
  if (
    missionId === undefined ||
    missionId === null ||
    String(missionId).trim() === ""
  ) {
    throw new Error("A valid mission ID is required.");
  }

  const response = await api.get(
    `/simulator/missions/${encodeURIComponent(missionId)}/digital-twin/`
  );

  const data = response.data;

  if (
    !data ||
    data.success !== true ||
    !data.mission ||
    !data.crew_health ||
    !data.habitat ||
    !data.health_alerts ||
    !data.data_provenance
  ) {
    throw new Error(
      "Invalid Mission Digital Twin summary received from API."
    );
  }

  return data;
}
