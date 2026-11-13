import { create } from "zustand";
import { getDashboardAnalytics } from "./dashboardService";

function getErrorMessage(error) {
  const data = error.response?.data;

  if (data?.detail) return data.detail;
  if (typeof data === "string") return data;

  return error.message || "Unable to load dashboard analytics.";
}

const useDashboardStore = create((set, get) => ({
  analytics: null,
  isLoading: false,
  error: null,
  lastFetchedAt: null,

  fetchAnalytics: async () => {
    if (get().isLoading) {
      return get().analytics;
    }

    set({ isLoading: true, error: null });

    try {
      const analytics = await getDashboardAnalytics();

      set({
        analytics,
        isLoading: false,
        error: null,
        lastFetchedAt: new Date().toISOString(),
      });

      return analytics;
    } catch (error) {
      set({
        isLoading: false,
        error: getErrorMessage(error),
      });

      throw error;
    }
  },

  clearAnalytics: () => {
    set({
      analytics: null,
      isLoading: false,
      error: null,
      lastFetchedAt: null,
    });
  },
}));

export default useDashboardStore;
