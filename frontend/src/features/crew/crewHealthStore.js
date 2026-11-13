import { create } from "zustand";

import {
  getAstronauts,
  getHealthReadings,
  getAstronautById,
  getHealthReadingAnalysis,
} from "./crewHealthService";

function getErrorMessage(error) {
  const data = error.response?.data;

  if (data?.detail) {
    return data.detail;
  }

  if (typeof data === "string") {
    return data;
  }

  if (data && typeof data === "object") {
    const firstValue = Object.values(data)[0];

    if (Array.isArray(firstValue)) {
      return String(firstValue[0]);
    }

    if (typeof firstValue === "string") {
      return firstValue;
    }
  }

  return error.message || "Unable to load crew health data.";
}

const useCrewHealthStore = create((set, get) => ({
  astronauts: [],
  readings: [],

  selectedAstronaut: null,
  selectedAnalysis: null,

  isLoading: false,
  isDetailLoading: false,

  error: null,
  detailError: null,

  lastFetchedAt: null,

  fetchCrewHealth: async ({ force = false } = {}) => {
    if (get().isLoading) {
      return null;
    }

    if (
      !force &&
      get().lastFetchedAt &&
      get().astronauts.length >= 0
    ) {
      // Explicit refresh remains available through force=true.
      // This branch intentionally does not block normal navigation.
    }

    set({
      isLoading: true,
      error: null,
    });

    try {
      const [astronauts, readings] = await Promise.all([
        getAstronauts(),
        getHealthReadings(),
      ]);

      set({
        astronauts,
        readings,
        isLoading: false,
        error: null,
        lastFetchedAt: new Date().toISOString(),
      });

      return { astronauts, readings };
    } catch (error) {
      set({
        isLoading: false,
        error: getErrorMessage(error),
      });

      throw error;
    }
  },

  fetchAstronautDetail: async (id) => {
    set({
      isDetailLoading: true,
      detailError: null,
      selectedAnalysis: null,
    });

    try {
      const astronaut = await getAstronautById(id);

      set({
        selectedAstronaut: astronaut,
        isDetailLoading: false,
        detailError: null,
      });

      return astronaut;
    } catch (error) {
      set({
        isDetailLoading: false,
        detailError: getErrorMessage(error),
      });

      throw error;
    }
  },

  fetchReadingAnalysis: async (readingId) => {
    try {
      const analysis = await getHealthReadingAnalysis(readingId);

      set({
        selectedAnalysis: analysis,
        detailError: null,
      });

      return analysis;
    } catch (error) {
      set({
        detailError: getErrorMessage(error),
      });

      throw error;
    }
  },

  clearSelectedAstronaut: () => {
    set({
      selectedAstronaut: null,
      selectedAnalysis: null,
      detailError: null,
    });
  },

  clearCrewHealth: () => {
    set({
      astronauts: [],
      readings: [],
      selectedAstronaut: null,
      selectedAnalysis: null,
      isLoading: false,
      isDetailLoading: false,
      error: null,
      detailError: null,
      lastFetchedAt: null,
    });
  },
}));

export default useCrewHealthStore;
