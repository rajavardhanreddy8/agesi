import axios from 'axios';
// Trigger build: 2026-02-08 10:55 AM

// Helper function to normalize base URL
const normalizeBaseURL = (url: string | undefined): string => {
    if (!url) {
        return 'https://outing-backend-api.azurewebsites.net/api';
    }

    // Remove trailing slashes
    url = url.replace(/\/+$/, '');

    // If URL doesn't end with /api, add it
    if (!url.endsWith('/api')) {
        url = url + '/api';
    }

    return url;
};

const baseURL = normalizeBaseURL(import.meta.env.VITE_API_URL);

const api = axios.create({
    baseURL: baseURL,
    headers: {
        'Content-Type': 'application/json',
    },
});

console.log('API Base URL:', api.defaults.baseURL);

// Add a request interceptor to add the auth token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Add a response interceptor to handle 401 errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            // Only redirect if not already on login page to avoid loops
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;
