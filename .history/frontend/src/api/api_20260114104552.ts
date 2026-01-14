import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터: 토큰 추가
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

// 응답 인터셉터: 401 에러 시 로그인 페이지로 리다이렉트
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface User {
  id: number;
  employee_id: string;
  name: string;
  email: string;
}

export interface System {
  id: number;
  system_name: string;
  description?: string;
}

export interface CheckItem {
  id: number;
  system_id: number;
  item_name: string;
  description?: string;
  order_index: number;
  special_notes: string[];
}

export interface ChecklistRecord {
  id: number;
  user_id: number;
  check_item_id: number;
  check_date: string;
  status: 'PASS' | 'FAIL';
  notes?: string;
  checked_at: string;
}

export interface ChecklistSubmitItem {
  check_item_id: number;
  status: 'PASS' | 'FAIL';
  notes?: string;
}

export const authAPI = {
  login: async (employeeId: string, password: string) => {
    const formData = new FormData();
    formData.append('username', employeeId);
    formData.append('password', password);
    const response = await api.post('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export const userAPI = {
  getMe: async (): Promise<User> => {
    const response = await api.get('/api/user/me');
    return response.data;
  },
  getSystems: async (): Promise<System[]> => {
    const response = await api.get('/api/user/systems');
    return response.data;
  },
};

export const checklistAPI = {
  getCheckItems: async (systemId: number): Promise<CheckItem[]> => {
    const response = await api.get(`/api/systems/${systemId}/check-items`);
    return response.data;
  },
  getTodayChecklist: async (): Promise<ChecklistRecord[]> => {
    const response = await api.get('/api/checklist/today');
    return response.data;
  },
  submitChecklist: async (items: ChecklistSubmitItem[]) => {
    const response = await api.post('/api/checklist/submit', { items });
    return response.data;
  },
  getUncheckedItems: async () => {
    const response = await api.get('/api/checklist/unchecked');
    return response.data;
  },
};

export default api;

