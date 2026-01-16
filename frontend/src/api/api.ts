import axios from "axios";

// 현재 호스트에 맞춰 백엔드 URL 동적 설정
const getApiBaseUrl = (): string => {
  // 환경 변수가 설정되어 있으면 우선 사용
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }

  // 현재 호스트와 포트 가져오기
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;

  // localhost나 127.0.0.1이면 localhost:8003 사용
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return "http://localhost:8003";
  }

  // 그 외의 경우 (예: 192.10.10.206) 같은 호스트의 8003 포트 사용
  return `${protocol}//${hostname}:8003`;
};

const API_BASE_URL = getApiBaseUrl();

// 디버깅: API URL 확인
// console.log("API Base URL:", API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// 요청 인터셉터: 토큰 추가
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // 디버깅: 요청 URL 확인
    // console.log("API Request:", config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error("API Request Error:", error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터: 401 에러 시 로그인 페이지로 리다이렉트
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 디버깅: 에러 정보 확인
    if (error.response) {
      console.error("API Response Error:", error.response.status, error.response.data);
    } else if (error.request) {
      console.error("API Request Failed - No Response:", error.request);
      console.error("Request URL:", error.config?.url);
      console.error("Full Error:", error);
    } else {
      console.error("API Error:", error.message);
    }
    
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export interface User {
  id: number;
  employee_id: string;
  division: string;
  general_headquarters: string;
  headquarters: string;
  name: string;
  email: string;
  console_role: boolean;
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
}

export interface ChecklistRecord {
  id: number;
  user_id: number;
  check_item_id: number;
  check_date: string;
  status: "PASS" | "FAIL";
  notes?: string;
  checked_at: string;
}

export interface ChecklistSubmitItem {
  check_item_id: number;
  status: "PASS" | "FAIL";
  notes?: string;
}

export const authAPI = {
  login: async (employeeId: string, password: string) => {
    const formData = new FormData();
    formData.append("username", employeeId);
    formData.append("password", password);
    const response = await api.post("/api/auth/login", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },
};

export const userAPI = {
  getMe: async (): Promise<User> => {
    const response = await api.get("/api/user/me");
    return response.data;
  },
  getSystems: async (): Promise<System[]> => {
    const response = await api.get("/api/user/systems");
    return response.data;
  },
};

export const checklistAPI = {
  getCheckItems: async (systemId: number): Promise<CheckItem[]> => {
    const response = await api.get(`/api/systems/${systemId}/check-items`);
    return response.data;
  },
  getTodayChecklist: async (): Promise<ChecklistRecord[]> => {
    const response = await api.get("/api/checklist/today");
    return response.data;
  },
  submitChecklist: async (items: ChecklistSubmitItem[]) => {
    const response = await api.post("/api/checklist/submit", { items });
    return response.data;
  },
  getUncheckedItems: async () => {
    const response = await api.get("/api/checklist/unchecked");
    return response.data;
  },
};

export interface SchedulerJob {
  id: string;
  name: string;
  next_run_time: string | null;
}

export interface SchedulerStatus {
  running: boolean;
  jobs: SchedulerJob[];
}

export const schedulerAPI = {
  testEmail: async (hour: number, minute: number) => {
    const response = await api.post("/api/scheduler/test-email", {
      hour,
      minute,
    });
    return response.data;
  },
  testEmailNow: async () => {
    const response = await api.post("/api/scheduler/test-email-now");
    return response.data;
  },
  getStatus: async (): Promise<SchedulerStatus> => {
    const response = await api.get("/api/scheduler/status");
    return response.data;
  },
  cancelJob: async (jobId: string) => {
    const response = await api.delete(`/api/scheduler/jobs/${jobId}`);
    return response.data;
  },
};

export interface ConsoleStats {
  pass_count: number;
  fail_count: number;
  unchecked_count: number;
}

export interface ConsoleFailItem {
  id: number;
  system_id: number;
  system_name: string;
  check_item_id: number;
  item_name: string;
  notes?: string;
  fail_time: string;
  user_id: number;
  user_name: string;
  employee_id: string;
  is_resolved: boolean;
  resolved_date?: string;
  resolved_time?: string;
}

export interface ExcelExportRequest {
  start_date: string; // YYYY-MM-DD
  end_date: string; // YYYY-MM-DD
}

export const consoleAPI = {
  getStats: async (): Promise<ConsoleStats> => {
    const response = await api.get("/api/console/stats");
    return response.data;
  },
  getFailItems: async (): Promise<ConsoleFailItem[]> => {
    const response = await api.get("/api/console/fail-items");
    return response.data;
  },
  exportExcel: async (request: ExcelExportRequest): Promise<Blob> => {
    const response = await api.post(
      "/api/console/export-excel",
      request,
      {
        responseType: "blob",
      }
    );
    return response.data;
  },
};

export default api;
