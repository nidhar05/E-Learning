import axios from "axios";

const DEFAULT_API_BASE_URL = "http://localhost:8000/api/";

const normalizedBaseUrl = (
  process.env.NEXT_PUBLIC_API_BASE_URL || DEFAULT_API_BASE_URL
).replace(/\/?$/, "/");

const AUTH_EXCLUDED_PATHS = [
  "users/login/",
  "users/signup/",
  "users/refresh/",
];

const api = axios.create({
  baseURL: normalizedBaseUrl,
  headers: {
    "Content-Type": "application/json",
  },
});

const shouldSkipAuth = (url = "") =>
  AUTH_EXCLUDED_PATHS.some((path) => url?.includes(path));

const clearAuthStorage = () => {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
  window.dispatchEvent(new Event("auth:logout"));
};

let refreshPromise = null;

const refreshAccessToken = async () => {
  if (typeof window === "undefined") {
    return null;
  }

  const refreshToken = localStorage.getItem("refresh_token");

  if (
    !refreshToken ||
    refreshToken === "undefined" ||
    refreshToken === "null"
  ) {
    clearAuthStorage();
    return null;
  }

  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${normalizedBaseUrl}users/refresh/`, {
        refresh: refreshToken,
      })
      .then((response) => {
        const newAccessToken = response.data?.access;

        if (!newAccessToken) {
          clearAuthStorage();
          return null;
        }

        localStorage.setItem("access_token", newAccessToken);
        return newAccessToken;
      })
      .catch((error) => {
        clearAuthStorage();
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
};

// Request interceptor to add the auth token to every request
api.interceptors.request.use(
  (config) => {
    // Only access localStorage if in the browser
    if (typeof window !== "undefined") {
      let token = localStorage.getItem("access_token");

      // Prevent attaching invalid token strings (like "undefined" or "null")
      if (token && token !== "undefined" && token !== "null") {
        // Do not attach token to auth requests.
        if (!shouldSkipAuth(config.url)) {
          config.headers = config.headers ?? {};
          config.headers["Authorization"] = `Bearer ${token}`;
        }
      } else {
        // Clear broken tokens
        clearAuthStorage();
      }
    }

    if (config.data instanceof FormData) {
      config.headers = config.headers ?? {};
      delete config.headers["Content-Type"];
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor to handle token expiration
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !shouldSkipAuth(originalRequest.url)
    ) {
      originalRequest._retry = true;

      try {
        const newAccessToken = await refreshAccessToken();

        if (newAccessToken) {
          originalRequest.headers = originalRequest.headers ?? {};
          originalRequest.headers["Authorization"] = `Bearer ${newAccessToken}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        console.warn("Unauthorized! Session refresh failed.", refreshError);
      }
    }

    if (error.response?.status === 401) {
      clearAuthStorage();
    }

    return Promise.reject(error);
  },
);

export default api;
