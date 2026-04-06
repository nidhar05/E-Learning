"use client";

import React, { createContext, useContext, useSyncExternalStore } from "react";
import api from "../api/client";

const AuthContext = createContext();
const AUTH_CHANGE_EVENT = "auth:change";
const AUTH_LOGOUT_EVENT = "auth:logout";
const UNHYDRATED = Symbol("auth-unhydrated");

let cachedToken = null;
let cachedUserData = null;
let cachedUserSnapshot = null;

const resetCachedUser = () => {
  cachedToken = null;
  cachedUserData = null;
  cachedUserSnapshot = null;
};

const getAuthSnapshot = () => {
  const token = localStorage.getItem("access_token");
  const userData = localStorage.getItem("user");

  if (!token || !userData) {
    resetCachedUser();
    return null;
  }

  if (token === cachedToken && userData === cachedUserData) {
    return cachedUserSnapshot;
  }

  try {
    cachedToken = token;
    cachedUserData = userData;
    cachedUserSnapshot = JSON.parse(userData);
    return cachedUserSnapshot;
  } catch {
    resetCachedUser();
    return null;
  }
};

const getServerAuthSnapshot = () => UNHYDRATED;

const subscribeToAuth = (callback) => {
  if (typeof window === "undefined") {
    return () => {};
  }

  window.addEventListener("storage", callback);
  window.addEventListener(AUTH_CHANGE_EVENT, callback);
  window.addEventListener(AUTH_LOGOUT_EVENT, callback);

  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener(AUTH_CHANGE_EVENT, callback);
    window.removeEventListener(AUTH_LOGOUT_EVENT, callback);
  };
};

const emitAuthChange = (eventName = AUTH_CHANGE_EVENT) => {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(new Event(eventName));
};

const clearStoredAuth = () => {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
  resetCachedUser();
  emitAuthChange(AUTH_LOGOUT_EVENT);
};

export const AuthProvider = ({ children }) => {
  const authSnapshot = useSyncExternalStore(
    subscribeToAuth,
    getAuthSnapshot,
    getServerAuthSnapshot,
  );
  const loading = authSnapshot === UNHYDRATED;
  const user = loading ? null : authSnapshot;

  const login = async (username, password) => {
    try {
      const response = await api.post("users/login/", { username, password });
      const { access_token, refresh_token, user: userData } = response.data;

      localStorage.setItem("access_token", access_token);
      localStorage.setItem("refresh_token", refresh_token);
      localStorage.setItem("user", JSON.stringify(userData));

      emitAuthChange();
      return { success: true };
    } catch (error) {
      if (error.response?.status === 401) {
        clearStoredAuth();

        return {
          success: false,
          error:
            "Invalid username or password. If you're running the local database for the first time, create an account first.",
        };
      }

      console.error("Login failure", error);
      return {
        success: false,
        error:
          error.response?.data?.error ||
          "Login failed. Please try again.",
      };
    }
  };

  const signup = async (userData) => {
    try {
      await api.post("users/signup/", userData);
      // Auto-login after successful signup
      return await login(userData.username, userData.password);
    } catch (error) {
      console.error("Signup failure", error);
      return {
        success: false,
        error:
          error.response?.data || "Signup failed. Please check your inputs.",
      };
    }
  };

  const logout = () => {
    clearStoredAuth();
  };

  return (
    <AuthContext.Provider value={{ user, login, signup, logout, loading }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
