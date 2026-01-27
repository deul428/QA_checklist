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
      console.error(
        "API Response Error:",
        error.response.status,
        error.response.data
      );
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
  user_id: string;
  user_name: string;
  user_email: string;
  division?: string;
  general_headquarters?: string;
  department?: string;
  headquarters?: string;
  position?: string;
  role?: string;
  console_role: boolean;
}

export interface System {
  system_id: number;
  system_name: string;
  system_description?: string;
  has_dev: boolean;
  has_stg: boolean;
  has_prd: boolean;
}

export interface CheckItem {
  item_id: number;
  system_id: number;
  item_name: string;
  item_description?: string;
  environment: string; // 'dev', 'stg', 'prd'
  status: "active" | "deleted"; // 'active' or 'deleted'
}

export interface ChecklistRecord {
  records_id: number;
  user_id: string;
  check_item_id: number;  // API 응답은 check_item_id를 반환함
  system_id?: number;  // 시스템 ID (denormalized)
  check_date: string;
  environment: string; // 'dev', 'stg', 'prd'
  status: "PASS" | "FAIL";
  fail_notes?: string;
  checked_at: string;
}

export interface ChecklistSubmitItem {
  check_item_id: number;
  status: "PASS" | "FAIL";
  fail_notes?: string;
  environment: string; // 'dev', 'stg', 'prd'
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
  searchUsers: async (query: string): Promise<User[]> => {
    const response = await api.get("/api/user/search", {
      params: { query },
    });
    return response.data;
  },
};

export const checklistAPI = {
  getCheckItems: async (systemId: number, environment: string = "prd"): Promise<CheckItem[]> => {
    const response = await api.get(`/api/systems/${systemId}/check-items`, {
      params: { environment },
    });
    return response.data;
  },
  getTodayChecklist: async (environment: string = "prd"): Promise<ChecklistRecord[]> => {
    const response = await api.get("/api/checklist/today", {
      params: { environment },
    });
    return response.data;
  },
  submitChecklist: async (items: ChecklistSubmitItem[]) => {
    const response = await api.post("/api/checklist/submit", { items });
    return response.data;
  },
  getUncheckedItems: async (environment?: string) => {
    const params = environment ? { environment } : {};
    const response = await api.get("/api/checklist/unchecked", { params });
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
  environment: string; // 'dev', 'stg', 'prd'
  fail_notes?: string;
  fail_time: string;
  user_id: string;
  user_name: string;
  is_resolved: boolean;
  resolved_date?: string;
  resolved_time?: string;
}

export interface ConsoleAllItem {
  id: number;
  system_id: number;
  system_name: string;
  check_item_id: number;
  item_name: string;
  environment: string;
  status: "PASS" | "FAIL" | "미점검";
  fail_notes?: string;
  fail_time?: string;
  user_id?: string;
  user_name?: string;
  is_resolved: boolean;
  resolved_time?: string;
  checked_at?: string;
}

export interface ExcelExportRequest {
  start_date: string; // YYYY-MM-DD
  end_date: string; // YYYY-MM-DD
}

export const consoleAPI = {
  getStats: async (environment?: string): Promise<ConsoleStats> => {
    const params = environment ? { environment } : {};
    const response = await api.get("/api/console/stats", { params });
    return response.data;
  },
  getFailItems: async (environment?: string): Promise<ConsoleFailItem[]> => {
    const params = environment ? { environment } : {};
    const response = await api.get("/api/console/fail-items", { params });
    return response.data;
  },
  getAllItems: async (environment?: string): Promise<ConsoleAllItem[]> => {
    const params = environment ? { environment } : {};
    const response = await api.get("/api/console/all-items", { params });
    return response.data;
  },
  exportExcel: async (request: ExcelExportRequest): Promise<Blob> => {
    const response = await api.post("/api/console/export-excel", request, {
      responseType: "blob",
    });
    return response.data;
  },
};


export interface CheckItemCreate {
  system_id: number;
  item_name: string;
  item_description?: string;
  environment: string; // 'dev', 'stg', 'prd' (필수)
  apply_to_all_environments?: boolean; // 일괄 처리 여부
  user_ids?: string[]; // 담당자 ID 목록 (항목 생성 시 함께 배정)
}

export interface CheckItemUpdate {
  item_name?: string;
  item_description?: string;
  status?: string;
  apply_to_all_environments?: boolean; // 일괄 처리 여부
}

export interface Assignment {
  id: number;
  user_id: string;
  user_name: string;
  system_id: number;
  system_name: string;
  item_name: string;
  created_at: string;
}

export interface AssignmentCreate {
  system_id: number;
  check_item_id: number;
  user_ids: string[];
}

export interface SubstituteAssignment {
  id: number;
  original_user_id: string;
  original_user_name: string;
  substitute_user_id: string;
  substitute_user_name: string;
  system_id: number;
  system_name: string;
  start_date: string; // YYYY-MM-DD
  end_date: string; // YYYY-MM-DD
  created_at: string;
  is_active: boolean;
}

export interface SubstituteAssignmentCreate {
  substitute_user_id: string;
  system_id: number;
  start_date: string; // YYYY-MM-DD
  end_date: string; // YYYY-MM-DD
}

export const listAPI = {
  getSystems: async (): Promise<System[]> => {
    const response = await api.get("/api/list/systems");
    return response.data;
  },
  getCheckItems: async (systemId?: number, environment?: string): Promise<CheckItem[]> => {
    const params: any = {};
    if (systemId) params.system_id = systemId;
    if (environment) params.environment = environment;
    const response = await api.get("/api/list/check-items", { params });
    return response.data;
  },
  createCheckItem: async (data: CheckItemCreate): Promise<CheckItem[]> => {
    const response = await api.post("/api/list/check-items", data);
    return response.data;
  },
  updateCheckItem: async (
    itemId: number,
    data: CheckItemUpdate
  ): Promise<CheckItem[]> => {
    const response = await api.put(`/api/list/check-items/${itemId}`, data);
    return response.data;
  },
  deleteCheckItem: async (itemId: number, applyToAllEnvironments: boolean = false): Promise<void> => {
    await api.delete(`/api/list/check-items/${itemId}`, {
      params: { apply_to_all_environments: applyToAllEnvironments },
    });
  },
  getUsers: async (): Promise<User[]> => {
    const response = await api.get("/api/list/users");
    return response.data;
  },
  getAssignments: async (
    systemId?: number,
    checkItemId?: number
  ): Promise<Assignment[]> => {
    const params: any = {};
    if (systemId) params.system_id = systemId;
    if (checkItemId) params.check_item_id = checkItemId;
    // environment 파라미터 제거 (환경 무관하게 배정)
    const response = await api.get("/api/list/assignments", { params });
    return response.data;
  },
  createAssignments: async (
    data: AssignmentCreate
  ): Promise<{ message: string; created_count: number }> => {
    const response = await api.post("/api/list/assignments", data);
    return response.data;
  },
  deleteAssignment: async (assignmentId: number): Promise<void> => {
    await api.delete(`/api/list/assignments/${assignmentId}`);
  },
};

export const substituteAPI = {
  create: async (
    data: SubstituteAssignmentCreate
  ): Promise<SubstituteAssignment> => {
    const response = await api.post("/api/substitute/create", data);
    return response.data;
  },
  list: async (): Promise<SubstituteAssignment[]> => {
    const response = await api.get("/api/substitute/list");
    return response.data;
  },
  getActive: async (): Promise<SubstituteAssignment[]> => {
    const response = await api.get("/api/substitute/active");
    return response.data;
  },
  delete: async (substituteId: number): Promise<void> => {
    await api.delete(`/api/substitute/${substituteId}`);
  },
};

export default api;
