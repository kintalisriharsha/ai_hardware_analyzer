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

export const getFanInfo = () => api.get('/fans/');

// Add this new function to fetch system information
export const getSystemInfo = async () => {
  try {
    const response = await fetch("/api/system-info/");
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.json();

    // If fan data is not included in system info, fetch it separately and merge
    if (!data.fans || !data.fans.length) {
      try {
        const fanData = await getFanInfo();
        if (fanData && fanData.length) {
          data.fans = {
            fans: fanData,
            hasFans: true,
          };
        }
      } catch (fanError) {
        console.error("Error fetching fan data:", fanError);
        // Continue without fan data if it fails
      }
    }

    return data;
  } catch (error) {
    console.error("Error fetching system information:", error);
    throw error;
  }
};


export default api;
