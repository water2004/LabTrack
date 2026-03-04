import axios from 'axios';

export const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    // HTTP headers must be ISO-8859-1. We encode the token (which might be a Chinese username)
    // to Base64 to ensure it's safe for the Authorization header.
    try {
      const safeToken = btoa(encodeURIComponent(token).replace(/%([0-9A-F]{2})/g, (_match, p1) => {
          return String.fromCharCode(parseInt(p1, 16));
      }));
      config.headers.Authorization = `Bearer ${safeToken}`;
    } catch (e) {
      // Fallback for cases where token might already be safe or btoa fails
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export default api;
