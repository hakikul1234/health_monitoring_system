import { create } from "zustand";

import {
  getSimulatorAstronauts,
  getSimulatorMissions,
  generateTelemetry,
  getVirtualHealthSensors,
  registerVirtualHealthSensor,
  simulateVirtualSensor,
  getVirtualSensorRuns,
  evaluateReadingTrust,
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

  virtualSensors: [],
  sensorRuns: [],
  sensorResult: null,
  isLoadingSensors: false,
  isRegisteringSensor: false,
  isRunningSensor: false,
  sensorError: null,

  trustDecision: null,
  isEvaluatingTrust: false,
  trustDecisionError: null,

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

  fetchVirtualSensors: async () => {
    set({
      isLoadingSensors: true,
      sensorError: null,
    });

    try {
      const [virtualSensors, sensorRuns] = await Promise.all([
        getVirtualHealthSensors(),
        getVirtualSensorRuns(),
      ]);

      set({
        virtualSensors,
        sensorRuns,
        isLoadingSensors: false,
        sensorError: null,
      });

      return { virtualSensors, sensorRuns };
    } catch (error) {
      set({
        isLoadingSensors: false,
        sensorError: getErrorMessage(error),
      });

      throw error;
    }
  },

  registerSensor: async (payload) => {
    set({
      isRegisteringSensor: true,
      sensorError: null,
    });

    try {
      const sensor = await registerVirtualHealthSensor(payload);
      const virtualSensors = await getVirtualHealthSensors();

      set({
        virtualSensors,
        isRegisteringSensor: false,
        sensorError: null,
      });

      return sensor;
    } catch (error) {
      set({
        isRegisteringSensor: false,
        sensorError: getErrorMessage(error),
      });

      throw error;
    }
  },

  runVirtualSensorSimulation: async (sensorId, payload) => {
    set({
      isRunningSensor: true,
      sensorError: null,
      sensorResult: null,
    });

    try {
      const result = await simulateVirtualSensor(sensorId, payload);
      const sensorRuns = await getVirtualSensorRuns();

      set({
        sensorResult: result,
        sensorRuns,
        isRunningSensor: false,
        sensorError: null,
      });

      return result;
    } catch (error) {
      set({
        isRunningSensor: false,
        sensorError: getErrorMessage(error),
      });

      throw error;
    }
  },

  evaluateReadingTrust: async (payload) => {
    set({
      isEvaluatingTrust: true,
      trustDecision: null,
      trustDecisionError: null,
    });

    try {
      const result = await evaluateReadingTrust(payload);

      set({
        trustDecision: result,
        isEvaluatingTrust: false,
        trustDecisionError: null,
      });

      return result;
    } catch (error) {
      const message = getErrorMessage(error);

      set({
        isEvaluatingTrust: false,
        trustDecisionError: message,
      });

      throw error;
    }
  },

  clearTrustDecision: () => {
    set({
      trustDecision: null,
      trustDecisionError: null,
      isEvaluatingTrust: false,
    });
  },

  clearSensorResult: () => {
    set({
      sensorResult: null,
      sensorError: null,
    });
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
