import axios from 'axios';

// Создаем экземпляр axios для основного API
const api = axios.create({
    baseURL: '/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Создаем экземпляр axios для admin API
export const adminApiInstance = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Callback logic for auth
let authUpdateCallback = () => { };
let authErrorCallback = () => { };

export const setAuthUpdateCallback = (callback: () => void) => {
    authUpdateCallback = callback;
};

export const setAuthErrorCallback = (callback: () => void) => {
    authErrorCallback = callback;
};

export const triggerAuthUpdate = () => {
    authUpdateCallback();
};

export const triggerAuthError = () => {
    authErrorCallback();
};

export default api;
