import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Conflict Proneness API
export const conflictPronenessAPI = {
  // Get all regions with conflict proneness scores
  getRegions: async () => {
    const response = await apiClient.get('/api/alerts/conflict-proneness');
    return response.data;
  },

  // Get all alerts sorted by proneness
  getAlerts: async (severity: string = 'ALL', limit: number = 100) => {
    const response = await apiClient.get('/api/alerts', {
      params: { severity, limit },
    });
    return response.data;
  },

  // Get dashboard statistics
  getDashboardStats: async () => {
    const response = await apiClient.get('/api/alerts/dashboard-stats');
    return response.data;
  },

  // Get full dashboard overview
  getDashboard: async () => {
    const response = await apiClient.get('/api/dashboard');
    return response.data;
  },
};

export default apiClient;
