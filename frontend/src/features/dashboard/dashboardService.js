import api from "../../lib/api";

export async function getDashboardAnalytics() {
  const response = await api.get("/missions/dashboard/analytics/");

  if (!response.data || response.data.success !== true) {
    throw new Error("Invalid dashboard analytics response.");
  }

  return response.data;
}
