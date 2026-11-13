import api from "../../lib/api";

export async function getAlerts(params = {}) {
  const response = await api.get("/alerts/", { params });
  const data = response.data;

  if (Array.isArray(data)) {
    return {
      results: data,
      count: data.length,
      next: null,
      previous: null,
    };
  }

  return {
    results: Array.isArray(data?.results) ? data.results : [],
    count: Number(data?.count ?? 0),
    next: data?.next ?? null,
    previous: data?.previous ?? null,
  };
}

export async function getAlertStatistics(params = {}) {
  const response = await api.get("/alerts/statistics/", {
    params,
  });

  return response.data?.statistics ?? {};
}

export async function getAlertById(id) {
  const response = await api.get(`/alerts/${id}/`);
  return response.data;
}

export async function acknowledgeAlert(id) {
  const response = await api.post(
    `/alerts/${id}/acknowledge/`
  );

  return response.data;
}

export async function resolveAlert(id, resolutionNotes) {
  const response = await api.post(
    `/alerts/${id}/resolve/`,
    {
      resolution_notes: resolutionNotes,
    }
  );

  return response.data;
}
