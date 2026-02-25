import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    // For this simple version, we pass token as a header or query param as needed.
    // The backend uses a simple check.
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
