const ACCESS_TOKEN_KEY = "astra_access_token";
const REFRESH_TOKEN_KEY = "astra_refresh_token";

export const tokenStorage = {
  getAccessToken() {
    return sessionStorage.getItem(ACCESS_TOKEN_KEY);
  },

  getRefreshToken() {
    return sessionStorage.getItem(REFRESH_TOKEN_KEY);
  },

  setTokens(access, refresh) {
    if (access) {
      sessionStorage.setItem(ACCESS_TOKEN_KEY, access);
    }

    if (refresh) {
      sessionStorage.setItem(REFRESH_TOKEN_KEY, refresh);
    }
  },

  setAccessToken(access) {
    if (access) {
      sessionStorage.setItem(ACCESS_TOKEN_KEY, access);
    }
  },

  clearTokens() {
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  },
};
