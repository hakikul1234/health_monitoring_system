import { create } from "zustand";

import {
  getSimulatorAstronauts,
  getSimulatorMissions,
  generateTelemetry,
} from "./simulatorService";

function getErrorMessage(error) {
  const data = error.response?.data;

  if (data?.detail) {
    return data.detail;
  }

  if (data?.message) {
    return data.message;
  }

  if (data?.errors && typeof data.errors === "object") {
    const firstValue = Object.values(data.errors)[0];

    if (Array.isArray(firstValue)) {
      return String(firstValue[0]);
    }

    if (typeof firstValue === "string") {
      return firstValue;
    }
  }

  return error.message || "Simulator request failed.";
}

const useSimulatorStore = create((set) => ({
  astronauts: [],
  missions: [],
  generationResult: null,

  isLoadingOptions: false,
  isGenerating: false,
  error: null,

  fetchSimulatorOptions: async () => {
    set({
      isLoadingOptions: true,
      error: null,
    });

    try {
      const [astronauts, missions] = await Promise.all([
        getSimulatorAstronauts(),
        getSimulatorMissions(),
      ]);

      set({
        astronauts,
        missions,
        isLoadingOptions: false,
        error: null,
      });

      return { astronauts, missions };
    } catch (error) {
      const message = getErrorMessage(error);

      set({
        isLoadingOptions: false,
        error: message,
      });

      throw error;
    }
  },

  runSimulation: async (payload) => {
    set({
      isGenerating: true,
      error: null,
      generationResult: null,
    });

    try {
      const result = await generateTelemetry(payload);

      set({
        generationResult: result,
        isGenerating: false,
        error: null,
      });

      return result;
    } catch (error) {
      const message = getErrorMessage(error);

      set({
        isGenerating: false,
        error: message,
      });

      throw error;
    }
  },

  clearGenerationResult: () => {
    set({
      generationResult: null,
      error: null,
    });
  },

  clearSimulator: () => {
    set({
      generationResult: null,
      error: null,
      isGenerating: false,
      isLoadingOptions: false,
    });
  },
}));

export default useSimulatorStore;