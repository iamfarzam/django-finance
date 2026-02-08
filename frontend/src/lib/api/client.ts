import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { ApiError } from './types';

// API base URL - uses relative path for Django integration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

// Get CSRF token from cookie
function getCSRFToken(): string | null {
  if (typeof document === 'undefined') return null;

  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [cookieName, cookieValue] = cookie.trim().split('=');
    if (cookieName === name) {
      return cookieValue;
    }
  }
  return null;
}

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies for session auth
});

// Request interceptor - add CSRF token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const csrfToken = getCSRFToken();
    if (csrfToken && config.headers) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    // Handle 401 - redirect to login
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
      }
    }

    // Handle 403 - forbidden
    if (error.response?.status === 403) {
      console.error('Access forbidden:', error.response.data);
    }

    // Handle 500 - server error
    if (error.response?.status === 500) {
      console.error('Server error:', error.response.data);
    }

    return Promise.reject(error);
  }
);

export { apiClient };

// Helper function for GET requests
export async function get<T>(url: string): Promise<T> {
  const response = await apiClient.get<T>(url);
  return response.data;
}

// Helper function for POST requests
export async function post<T, D = unknown>(url: string, data?: D): Promise<T> {
  const response = await apiClient.post<T>(url, data);
  return response.data;
}

// Helper function for PUT requests
export async function put<T, D = unknown>(url: string, data: D): Promise<T> {
  const response = await apiClient.put<T>(url, data);
  return response.data;
}

// Helper function for PATCH requests
export async function patch<T, D = unknown>(url: string, data: D): Promise<T> {
  const response = await apiClient.patch<T>(url, data);
  return response.data;
}

// Helper function for DELETE requests
export async function del<T = void>(url: string): Promise<T> {
  const response = await apiClient.delete<T>(url);
  return response.data;
}
