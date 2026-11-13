import { create } from "zustand";

import {
  getMissions,
  getMissionById,
  createMission,
  updateMission,
  deleteMission,
} from "./missionService";

function getErrorMessage(error) {
  const data = error.response?.data;

  if (typeof data === "string") {
    return data;
  }

  if (data?.detail) {
    return data.detail;
  }

  if (data?.non_field_errors?.length) {
    return String(data.non_field_errors[0]);
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

  return error.message || "Unable to complete mission operation.";
}

const useMissionStore = create((set, get) => ({
  missions: [],
  selectedMission: null,

  isLoading: false,
  isDetailLoading: false,
  isSaving: false,
  isDeleting: false,

  error: null,
  detailError: null,
  mutationError: null,

  lastFetchedAt: null,

  fetchMissions: async ({ force = false } = {}) => {
    if (get().isLoading) {
      return null;
    }

    if (
      !force &&
      get().lastFetchedAt &&
      get().missions.length >= 0
    ) {
      // Data can be refreshed explicitly using force=true.
      // Fetching remains available during normal navigation.
    }

    set({
      isLoading: true,
      error: null,
    });

    try {
      const missions = await getMissions();

      set({
        missions,
        isLoading: false,
        error: null,
        lastFetchedAt: new Date().toISOString(),
      });

      return missions;
    } catch (error) {
      set({
        isLoading: false,
        error: getErrorMessage(error),
      });

      throw error;
    }
  },

  fetchMissionDetail: async (id) => {
    set({
      isDetailLoading: true,
      detailError: null,
    });

    try {
      const mission = await getMissionById(id);

      set({
        selectedMission: mission,
        isDetailLoading: false,
        detailError: null,
      });

      return mission;
    } catch (error) {
      set({
        isDetailLoading: false,
        detailError: getErrorMessage(error),
      });

      throw error;
    }
  },

  addMission: async (missionData) => {
    set({
      isSaving: true,
      mutationError: null,
    });

    try {
      const mission = await createMission(missionData);

      set((state) => ({
        missions: [mission, ...state.missions],
        selectedMission: mission,
        isSaving: false,
        mutationError: null,
        lastFetchedAt: new Date().toISOString(),
      }));

      return mission;
    } catch (error) {
      set({
        isSaving: false,
        mutationError: getErrorMessage(error),
      });

      throw error;
    }
  },

  editMission: async (id, missionData) => {
    set({
      isSaving: true,
      mutationError: null,
    });

    try {
      const updatedMission = await updateMission(id, missionData);

      set((state) => ({
        missions: state.missions.map((mission) =>
          mission.id === updatedMission.id
            ? updatedMission
            : mission
        ),

        selectedMission:
          state.selectedMission?.id === updatedMission.id
            ? updatedMission
            : state.selectedMission,

        isSaving: false,
        mutationError: null,
        lastFetchedAt: new Date().toISOString(),
      }));

      return updatedMission;
    } catch (error) {
      set({
        isSaving: false,
        mutationError: getErrorMessage(error),
      });

      throw error;
    }
  },

  removeMission: async (id) => {
    set({
      isDeleting: true,
      mutationError: null,
    });

    try {
      await deleteMission(id);

      set((state) => ({
        missions: state.missions.filter(
          (mission) => mission.id !== id
        ),

        selectedMission:
          state.selectedMission?.id === id
            ? null
            : state.selectedMission,

        isDeleting: false,
        mutationError: null,
        lastFetchedAt: new Date().toISOString(),
      }));

      return true;
    } catch (error) {
      set({
        isDeleting: false,
        mutationError: getErrorMessage(error),
      });

      throw error;
    }
  },

  clearSelectedMission: () => {
    set({
      selectedMission: null,
      detailError: null,
    });
  },

  clearMutationError: () => {
    set({ mutationError: null });
  },

  clearMissions: () => {
    set({
      missions: [],
      selectedMission: null,
      isLoading: false,
      isDetailLoading: false,
      isSaving: false,
      isDeleting: false,
      error: null,
      detailError: null,
      mutationError: null,
      lastFetchedAt: null,
    });
  },
}));

export default useMissionStore;
