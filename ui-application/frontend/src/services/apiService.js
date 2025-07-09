import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    if (error.response?.status === 500) {
      console.error('Server Error:', error.response.data);
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  // Health check
  healthCheck: () => api.get('/health'),

  // Vendor endpoints
  getVendors: () => api.get('/vendors'),

  // File endpoints
  getFiles: (params = {}) => api.get('/files', { params }),
  getFileDetails: (fileName, vendor) => 
    api.get(`/file/${fileName}/details`, { params: { vendor } }),

  // Reconciliation endpoints
  getReconciliationResults: (params = {}) => 
    api.get('/reconciliation/results', { params }),
  getReconciliationSummary: (params = {}) => 
    api.get('/reconciliation/summary', { params }),

  // Account endpoints
  getAccounts: (params = {}) => api.get('/accounts', { params }),
  getAccountHistory: (accountId, params = {}) => 
    api.get(`/account/${accountId}/history`, { params }),

  // Dashboard endpoints
  getDashboardMetrics: (params = {}) => api.get('/dashboard/metrics', { params }),

  // Export endpoints
  exportReconciliationReport: (fileName, vendor) => 
    api.get('/export/reconciliation-report', { 
      params: { file_name: fileName, vendor } 
    }),
};

export default apiService;
