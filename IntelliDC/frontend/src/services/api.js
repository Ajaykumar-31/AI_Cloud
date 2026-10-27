import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor for tokens
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add a response interceptor to handle 401s globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Optional: automatically logout on 401 Unauthorized
      // localStorage.removeItem('token');
      // window.location.href = '/signin';
    }
    return Promise.reject(error);
  }
);

// Auth Services
export const authService = {
  login: (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    return api.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
  },
  getCurrentUser: () => api.get('/api/auth/me'),
};

// Server Services
export const serverService = {
  getServers: () => api.get('/api/servers'),
  getServer: (id) => api.get(`/api/servers/${id}`),
  createServer: (data) => api.post('/api/servers', data),
  updateServer: (id, data) => api.put(`/api/servers/${id}`, data),
  deleteServer: (id) => api.delete(`/api/servers/${id}`),
  getServerMetrics: (id) => api.get(`/api/servers/${id}/metrics`),
  postServerMetrics: (id, data) => api.post(`/api/servers/${id}/metrics`, data),
};

// IoT Services
export const iotService = {
  getDevices: () => api.get('/api/iot/devices'),
  getDevice: (id) => api.get(`/api/iot/devices/${id}`),
  createDevice: (data) => api.post('/api/iot/devices', data),
  updateDevice: (id, data) => api.put(`/api/iot/devices/${id}`, data),
  deleteDevice: (id) => api.delete(`/api/iot/devices/${id}`),
  postReading: (data) => api.post('/api/iot/readings', data),
  getDeviceReadings: (id, params) => api.get(`/api/iot/devices/${id}/readings`, { params }),
  getLatestThingSpeak: (deviceId) => api.get('/api/iot/thingspeak/latest', { params: { device_id: deviceId } }),
  getDeviceHistoricalReadings: (deviceId, params) => api.get(`/api/iot/devices/${deviceId}/historical`, { params }),
};

// Workload Services
export const workloadService = {
  getWorkloads: () => api.get('/api/workloads'),
  getWorkload: (id) => api.get(`/api/workloads/${id}`),
  createWorkload: (data) => api.post('/api/workloads', data),
  updateWorkload: (id, data) => api.put(`/api/workloads/${id}`, data),
  deleteWorkload: (id) => api.delete(`/api/workloads/${id}`),
};

// Alert Services
export const alertService = {
  getAlerts: () => api.get('/api/alerts'),
  getAlert: (id) => api.get(`/api/alerts/${id}`),
  acknowledgeAlert: (id) => api.post(`/api/alerts/${id}/acknowledge`),
  resolveAlert: (id) => api.post(`/api/alerts/${id}/resolve`),
  dismissAlert: (id) => api.post(`/api/alerts/${id}/dismiss`),
};

// AI Decision Services
export const aiService = {
  analyzeServer: (id) => api.post(`/api/ai/analyze/${id}`),
  getRecommendations: () => api.get('/api/ai/recommendations'),
  getRecommendation: (id) => api.get(`/api/ai/recommendations/${id}`),
  updateRecommendationStatus: (id, status) => api.patch(`/api/ai/recommendations/${id}/status`, { status }),
};

// Reports Services
export const reportService = {
  getInfrastructureReport: (params) => api.get('/api/reports/infrastructure', { params }),
  getIoTReport: (params) => api.get('/api/reports/iot', { params }),
  getEnergyReport: (params) => api.get('/api/reports/energy', { params }),
  getAlertReport: (params) => api.get('/api/reports/alerts', { params }),
  getAIReport: (params) => api.get('/api/reports/ai', { params }),
};

export default api;
