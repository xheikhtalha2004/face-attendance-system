/**
 * API Service - Centralized API client using axios
 * Handles all HTTP requests to backend
 */
import axios, { AxiosInstance, AxiosError } from 'axios';
import { API_BASE_URL, getAuthToken } from '../utils/apiConfig';

class APIService {
    private client: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Request interceptor - add JWT token
        this.client.interceptors.request.use(
            (config) => {
                const token = getAuthToken();
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor - handle errors
        this.client.interceptors.response.use(
            (response) => response,
            (error: AxiosError) => {
                if (error.response?.status === 401) {
                    // Unauthorized - clear token and redirect to login
                    localStorage.removeItem('token');
                    localStorage.removeItem('user');
                    window.location.href = '/';
                }
                return Promise.reject(error);
            }
        );
    }

    // ============================================
    // AUTHENTICATION
    // ============================================

    async login(email: string, password: string) {
        const response = await this.client.post('/auth/login', { email, password });
        return response.data;
    }

    async register(email: string, password: string, name: string) {
        const response = await this.client.post('/auth/register', { email, password, name });
        return response.data;
    }

    // ============================================
    // STUDENTS
    // ============================================

    async getStudents() {
        const response = await this.client.get('/students');
        return response.data;
    }

    async getStudent(id: string) {
        const response = await this.client.get(`/students/${id}`);
        return response.data;
    }

    async registerStudent(formData: FormData) {
        const response = await this.client.post('/students', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }

    async updateStudent(id: string, data: any) {
        const response = await this.client.put(`/students/${id}`, data);
        return response.data;
    }

    async deleteStudent(id: string) {
        const response = await this.client.delete(`/students/${id}`);
        return response.data;
    }

    // ============================================
    // ATTENDANCE
    // ============================================

    async getAttendance(filters?: { date?: string; studentId?: string }) {
        const params = new URLSearchParams();
        if (filters?.date) params.append('date', filters.date);
        if (filters?.studentId) params.append('studentId', filters.studentId);

        const response = await this.client.get(`/attendance?${params.toString()}`);
        return response.data;
    }

    async recognizeFace(frameBlob: Blob) {
        const formData = new FormData();
        formData.append('frame', frameBlob, 'frame.jpg');

        const response = await this.client.post('/recognize', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }

    async markAttendance(studentId: string, status: string, notes?: string) {
        const response = await this.client.post('/attendance/mark', {
            studentId,
            status,
            notes,
        });
        return response.data;
    }

    // ============================================
    // SETTINGS
    // ============================================

    async getSettings() {
        const response = await this.client.get('/settings');
        return response.data;
    }

    async updateSettings(settings: any) {
        const response = await this.client.put('/settings', settings);
        return response.data;
    }

    // ============================================
    // HEALTH CHECK
    // ============================================

    async healthCheck() {
        const response = await this.client.get('/health');
        return response.data;
    }
}

export const api = new APIService();
export default api;
