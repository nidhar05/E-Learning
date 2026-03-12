import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api/",
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add the auth token to every request
api.interceptors.request.use(
  (config) => {
    // Only access localStorage if in the browser
    if (typeof window !== "undefined") {
      let token = localStorage.getItem("access_token");
      
      // Prevent attaching invalid token strings (like "undefined" or "null")
      if (token && token !== "undefined" && token !== "null") {
        // Do not attach token to login or signup requests
        if (!config.url.includes("users/login/") && !config.url.includes("users/signup/")) {
          config.headers["Authorization"] = `Bearer ${token}`;
        }
      } else {
        // Clear broken tokens
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
      }
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
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn("Unauthorized! Token might be expired.");
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
      }
    }
    return Promise.reject(error);
  },
);

export default api;
