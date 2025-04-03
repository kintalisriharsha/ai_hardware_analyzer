/** @format */

// src/api.js
import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api";

// Create axios instance with auth headers
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add authorization header if token exists
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// API endpoints
export const getLatestMetrics = () => api.get("/metrics/latest/");
export const collectMetrics = () => api.post("/metrics/collect/");
export const getMetricsHistory = (params) => api.get("/metrics/", { params });
export const getMetricsStatistics = (days = 7) =>
  api.get(`/metrics/statistics/?days=${days}`);
export const getSystemSummary = () => api.get("/dashboard/");
export const getUnresolvedIssues = () => api.get("/issues/unresolved/");
export const resolveIssue = (id) => api.post(`/issues/${id}/resolve/`);
export const trainModel = (samples = 300) =>
  api.post("/training/train/", { samples });
export const login = (credentials) => api.post("/token/", credentials);
export const register = (userData) => api.post("/users/register/", userData);

// Fetch system metrics
export const fetchMetrics = async () => {
  const response = await api.get("/metrics/latest/");
  return response.data;
};

// Fetch hardware issues
export const fetchIssues = async (onlyUnresolved = false) => {
  const url = onlyUnresolved ? "/issues/unresolved/" : "/issues/";
  const response = await api.get(url);
  return response.data;
};

// Fetch dashboard data
export const fetchDashboardData = async () => {
  const response = await api.get("/dashboard/");
  return response.data;
};

export const getFanInfo = async () => {
  try {
    // Add a timestamp parameter to prevent caching
    const timestamp = new Date().getTime();
    const response = await fetch(`/api/fans/?t=${timestamp}`);

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();
    return { data };
  } catch (error) {
    console.error("Error fetching fan information:", error);

    // Return an error instead of fallback data to make issues more visible
    throw error;
  }
};

export const getFanData = async () => {
  // Add cache-busting parameter to prevent caching
  const timestamp = new Date().getTime();
  const response = await fetch(`/api/fan-data/?t=${timestamp}`);

  if (!response.ok) {
    throw new Error(`Error fetching fan data: ${response.status}`);
  }

  return response.json();
};

export default api;
