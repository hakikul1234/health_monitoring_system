import { create } from "zustand";

import api from "../lib/api";
import { tokenStorage } from "../lib/tokenStorage";

function getErrorMessage(error) {
  const data = error.response?.data;

  if (typeof data === "string") {
    return data;
  }

  if (data?.detail) {
    return data.detail;
  }

  if (data?.non_field_errors?.length) {
    return data.non_field_errors[0];
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

  return error.message || "Something went wrong.";
}

const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  startDemoSession: async () => {
    set({ isLoading: true, error: null });

    try {
      const sessionResponse = await api.post("/auth/demo-session/");
      const { access, refresh } = sessionResponse.data;

      if (!access || !refresh) {
        throw new Error("Invalid Mission Control demo session response.");
      }

      tokenStorage.setTokens(access, refresh);

      const userResponse = await api.get("/auth/me/");

      if (userResponse.data?.role !== "MISSION_CONTROL") {
        throw new Error("The demo session did not authenticate as Mission Control.");
      }

      set({
        user: userResponse.data,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      return userResponse.data;
    } catch (error) {
      tokenStorage.clearTokens();

      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: getErrorMessage(error),
      });

      return null;
    }
  },

  login: async (credentials) => {
    set({ isLoading: true, error: null });

    try {
      const loginResponse = await api.post(
        "/auth/login/",
        credentials
      );

      const { access, refresh } = loginResponse.data;

      if (!access || !refresh) {
        throw new Error("Invalid login response from server.");
      }

      tokenStorage.setTokens(access, refresh);

      const userResponse = await api.get("/auth/me/");

      set({
        user: userResponse.data,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      return userResponse.data;
    } catch (error) {
      tokenStorage.clearTokens();

      const message = getErrorMessage(error);

      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: message,
      });

      throw error;
    }
  },

  register: async (registrationData) => {
    set({ isLoading: true, error: null });

    try {
      const response = await api.post(
        "/auth/register/",
        registrationData
      );

      set({ isLoading: false, error: null });

      return response.data;
    } catch (error) {
      const message = getErrorMessage(error);

      set({
        isLoading: false,
        error: message,
      });

      throw error;
    }
  },

  fetchCurrentUser: async () => {
    const access = tokenStorage.getAccessToken();
    const refresh = tokenStorage.getRefreshToken();

    if (!access || !refresh) {
      tokenStorage.clearTokens();

      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });

      return null;
    }

    set({ isLoading: true, error: null });

    try {
      const response = await api.get("/auth/me/");

      set({
        user: response.data,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      return response.data;
    } catch (error) {
      tokenStorage.clearTokens();

      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: getErrorMessage(error),
      });

      return null;
    }
  },

  logout: () => {
    tokenStorage.clearTokens();

    set({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  },

  clearError: () => set({ error: null }),
}));

export default useAuthStore;
