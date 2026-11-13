import { create } from "zustand";

import {
  getAlerts,
  getAlertStatistics,
  getAlertById,
  acknowledgeAlert as acknowledgeAlertAPI,
  resolveAlert as resolveAlertAPI,
} from "./alertService";

const useAlertStore = create((set, get) => ({
  alerts: [],
  selectedAlert: null,
  statistics: {
    total_alerts: 0,
    open_alerts: 0,
    acknowledged_alerts: 0,
    resolved_alerts: 0,
    warning_alerts: 0,
    critical_alerts: 0,
  },

  totalCount: 0,
  next: null,
  previous: null,

  filters: {},
  isLoading: false,
  isDetailLoading: false,
  isMutating: false,

  error: null,
  detailError: null,
  mutationError: null,

  fetchAlerts: async (params = {}) => {
    set({
      isLoading: true,
      error: null,
      filters: { ...params },
    });

    try {
      const [list, statistics] = await Promise.all([
        getAlerts(params),
        getAlertStatistics(params),
      ]);

      set({
        alerts: list.results,
        totalCount: list.count,
        next: list.next,
        previous: list.previous,
        statistics,
        isLoading: false,
        error: null,
      });

      return list.results;
    } catch (error) {
      set({
        isLoading: false,
        error:
          error.response?.data?.detail ||
          error.response?.data?.message ||
          error.message ||
          "Unable to load health alerts.",
      });

      throw error;
    }
  },

  fetchAlertDetail: async (id) => {
    set({
      isDetailLoading: true,
      detailError: null,
    });

    try {
      const alert = await getAlertById(id);

      set({
        selectedAlert: alert,
        isDetailLoading: false,
        detailError: null,
      });

      return alert;
    } catch (error) {
      set({
        isDetailLoading: false,
        detailError:
          error.response?.data?.detail ||
          error.message ||
          "Unable to load alert details.",
      });

      throw error;
    }
  },

  acknowledgeAlert: async (id) => {
    set({
      isMutating: true,
      mutationError: null,
    });

    try {
      const response = await acknowledgeAlertAPI(id);

      await get().fetchAlerts(get().filters);

      set({
        selectedAlert: response.alert ?? null,
        isMutating: false,
        mutationError: null,
      });

      return response;
    } catch (error) {
      set({
        isMutating: false,
        mutationError:
          error.response?.data?.detail ||
          error.message ||
          "Unable to acknowledge alert.",
      });

      throw error;
    }
  },

  resolveAlert: async (id, resolutionNotes) => {
    set({
      isMutating: true,
      mutationError: null,
    });

    try {
      const response = await resolveAlertAPI(
        id,
        resolutionNotes
      );

      await get().fetchAlerts(get().filters);

      set({
        selectedAlert: response.alert ?? null,
        isMutating: false,
        mutationError: null,
      });

      return response;
    } catch (error) {
      set({
        isMutating: false,
        mutationError:
          error.response?.data?.detail ||
          error.message ||
          "Unable to resolve alert.",
      });

      throw error;
    }
  },

  clearSelectedAlert: () => {
    set({
      selectedAlert: null,
      detailError: null,
    });
  },

  clearMutationError: () => {
    set({ mutationError: null });
  },

  clearAlerts: () => {
    set({
      alerts: [],
      selectedAlert: null,
      statistics: {
        total_alerts: 0,
        open_alerts: 0,
        acknowledged_alerts: 0,
        resolved_alerts: 0,
        warning_alerts: 0,
        critical_alerts: 0,
      },
      totalCount: 0,
      next: null,
      previous: null,
      filters: {},
      isLoading: false,
      isDetailLoading: false,
      isMutating: false,
      error: null,
      detailError: null,
      mutationError: null,
    });
  },
}));

export default useAlertStore;
