import api from './api';

export const auth = {
    // Register new user
    register: async (data: any) => {
        const response = await api.post('/auth/register', data);
        return response.data;
    },

    // Login user
    login: async (credentials: any) => {
        const response = await api.post('/auth/login', credentials);
        if (response.data.success) {
            localStorage.setItem('token', response.data.token);
            localStorage.setItem('user', JSON.stringify(response.data.user));
        }
        return response.data;
    },

    // Verify email
    verifyEmail: async (token: string) => {
        const response = await api.post('/auth/verify-email', { token });
        return response.data;
    },

    // Logout
    logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
    },

    // Get current user from local storage
    getUser: () => {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    },

    // Check if authenticated
    isAuthenticated: () => {
        return !!localStorage.getItem('token');
    },

    // Update Profile
    updateProfile: async (data: any) => {
        const response = await api.put('/profile', data);
        return response.data;
    },

    // Get Profile
    getProfile: async () => {
        const response = await api.get('/profile');
        return response.data;
    }
};
