import axios from 'axios';

// Создаем экземпляр axios для основного API
const axiosInstance = axios.create({
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

export default axiosInstance;
