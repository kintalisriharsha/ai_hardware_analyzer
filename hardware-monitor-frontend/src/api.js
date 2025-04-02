import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

// Create axios instance with auth headers
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add authorization header if token exists
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// API endpoints
export const getLatestMetrics = () => api.get('/metrics/latest/');
export const collectMetrics = () => api.post('/metrics/collect/');
export const getMetricsHistory = (params) => api.get('/metrics/', { params });
export const getMetricsStatistics = (days = 7) => api.get(`/metrics/statistics/?days=${days}`);
export const getSystemSummary = () => api.get('/dashboard/');
export const getUnresolvedIssues = () => api.get('/issues/unresolved/');
export const resolveIssue = (id) => api.post(`/issues/${id}/resolve/`);
export const login = (credentials) => api.post('/token/', credentials);
export const register = (userData) => api.post('/users/register/', userData);
export const getSystemInfo = () => api.get('/system-info/');
export const getFanInfo = () => api.get("/fans/");

export const trainModel = async (samples = 300) => {
  try {
    const response = await fetch('/api/training/train/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ samples }),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || `HTTP error ${response.status}`);
    }
    
    return data;
  } catch (error) {
    console.error('Error training model:', error);
    throw error;
  }
};

export default api;