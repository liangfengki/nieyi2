import type {
  AdminDashboardStats,
  EmailCodeRequestResponse,
  LicenseCode,
  PlatformApiConfig,
  ProviderPreset,
  SessionResponse,
  StrategiesResponse,
  UserAPIConfig,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE || '';
const USER_SESSION_STORAGE_KEY = 'user_session_token';
const ADMIN_USERNAME_STORAGE_KEY = 'admin_username';
const ADMIN_PASSWORD_STORAGE_KEY = 'admin_password';

interface LicenseValidationResponse {
  valid: boolean;
  code: string;
  max_images: number | null;
  images_used: number;
  remaining: number | null;
  expires_at: string | null;
  note: string | null;
}

interface HistoryTask {
  status: string;
  images?: string[];
  plan_results?: unknown[];
}

interface HistoryResponse {
  tasks: HistoryTask[];
  total: number;
}

interface TaskStatusResponse {
  status: string;
  images?: string[];
  plan_results?: unknown[];
  error_message?: string;
  product_dna?: string;
  created_at?: string;
}

interface TaskSubmitResponse {
  task_id: string;
  status: string;
  message: string;
}

interface AdminLoginResponse {
  success: boolean;
  message: string;
}

interface CreateLicenseCodesResponse {
  codes: string[];
  count: number;
}

interface ConnectionTestResponse {
  success: boolean;
  message: string;
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');
  const payload: unknown = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const detail =
      typeof payload === 'object' && payload !== null && 'detail' in payload
        ? payload.detail
        : undefined;

    const rawMessage =
      typeof detail === 'string'
        ? detail
        : typeof payload === 'string' && payload
          ? payload
          : `请求失败 (${response.status})`;

    const message =
      response.status >= 500 && (rawMessage === 'Internal Server Error' || rawMessage.startsWith('请求失败'))
        ? '服务器开小差了，请稍后重试'
        : rawMessage;

    const error = new Error(message) as Error & {
      status: number;
      detail?: unknown;
      payload?: unknown;
    };
    error.status = response.status;
    error.detail = detail ?? message;
    error.payload = payload;
    throw error;
  }

  return payload as T;
}

function getUserSessionHeaders(): Record<string, string> {
  const token = localStorage.getItem(USER_SESSION_STORAGE_KEY) || '';
  return token ? { 'x-user-session': token } : {};
}

function getAdminHeaders(): Record<string, string> {
  const username = localStorage.getItem(ADMIN_USERNAME_STORAGE_KEY) || '';
  const password = localStorage.getItem(ADMIN_PASSWORD_STORAGE_KEY) || '';
  return username && password
    ? { 'x-admin-username': username, 'x-admin-password': password }
    : {};
}

function jsonHeaders(): Record<string, string> {
  return { ...getUserSessionHeaders(), 'Content-Type': 'application/json' };
}

function adminJsonHeaders(): Record<string, string> {
  return { ...getAdminHeaders(), 'Content-Type': 'application/json' };
}

export const api = {
  getStrategies: (): Promise<StrategiesResponse> =>
    fetch(`${API_BASE}/api/v1/prompts/strategies`).then((r) => parseJsonResponse<StrategiesResponse>(r)),

  requestEmailCode: (email: string): Promise<EmailCodeRequestResponse> =>
    fetch(`${API_BASE}/api/v1/session/request-email-code`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    }).then((r) => parseJsonResponse<EmailCodeRequestResponse>(r)),

  verifyEmailCode: (email: string, code: string): Promise<SessionResponse> =>
    fetch(`${API_BASE}/api/v1/session/verify-email-code`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, code }),
    }).then((r) => parseJsonResponse<SessionResponse>(r)),

  getSessionMe: (): Promise<SessionResponse> =>
    fetch(`${API_BASE}/api/v1/session/me`, {
      headers: getUserSessionHeaders(),
    }).then((r) => parseJsonResponse<SessionResponse>(r)),

  activateLicense: (code: string): Promise<SessionResponse> =>
    fetch(`${API_BASE}/api/v1/session/activate-license`, {
      method: 'POST',
      headers: jsonHeaders(),
      body: JSON.stringify({ code }),
    }).then((r) => parseJsonResponse<SessionResponse>(r)),

  validateLicense: (code: string): Promise<LicenseValidationResponse> =>
    fetch(`${API_BASE}/api/v1/license/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    }).then((r) => parseJsonResponse<LicenseValidationResponse>(r)),

  getProviderPresets: (): Promise<ProviderPreset[]> =>
    fetch(`${API_BASE}/api/v1/providers/presets`).then((r) => parseJsonResponse<ProviderPreset[]>(r)),

  getUserApiConfigs: (): Promise<UserAPIConfig[]> =>
    fetch(`${API_BASE}/api/v1/user/api-configs`, {
      headers: getUserSessionHeaders(),
    }).then((r) => parseJsonResponse<UserAPIConfig[]>(r)),

  createUserApiConfig: (config: unknown): Promise<UserAPIConfig> =>
    fetch(`${API_BASE}/api/v1/user/api-configs`, {
      method: 'POST',
      headers: jsonHeaders(),
      body: JSON.stringify(config),
    }).then((r) => parseJsonResponse<UserAPIConfig>(r)),

  updateUserApiConfig: (configId: string, config: unknown): Promise<Record<string, unknown>> =>
    fetch(`${API_BASE}/api/v1/user/api-configs/${configId}`, {
      method: 'PUT',
      headers: jsonHeaders(),
      body: JSON.stringify(config),
    }).then((r) => parseJsonResponse<Record<string, unknown>>(r)),

  deleteUserApiConfig: (configId: string): Promise<Record<string, unknown>> =>
    fetch(`${API_BASE}/api/v1/user/api-configs/${configId}`, {
      method: 'DELETE',
      headers: getUserSessionHeaders(),
    }).then((r) => parseJsonResponse<Record<string, unknown>>(r)),

  testUserConnection: (data: unknown): Promise<ConnectionTestResponse> =>
    fetch(`${API_BASE}/api/v1/user/test-connection`, {
      method: 'POST',
      headers: jsonHeaders(),
      body: JSON.stringify(data),
    }).then((r) => parseJsonResponse<ConnectionTestResponse>(r)),

  generate: (formData: FormData): Promise<TaskSubmitResponse> =>
    fetch(`${API_BASE}/api/v1/tasks/generate`, {
      method: 'POST',
      headers: getUserSessionHeaders(),
      body: formData,
    }).then((r) => parseJsonResponse<TaskSubmitResponse>(r)),

  getTask: (taskId: string): Promise<TaskStatusResponse> =>
    fetch(`${API_BASE}/api/v1/tasks/${taskId}`, {
      headers: getUserSessionHeaders(),
    }).then((r) => parseJsonResponse<TaskStatusResponse>(r)),

  getHistory: (limit = 50, offset = 0): Promise<HistoryResponse> =>
    fetch(`${API_BASE}/api/v1/tasks/history?limit=${limit}&offset=${offset}`, {
      headers: getUserSessionHeaders(),
    }).then((r) => parseJsonResponse<HistoryResponse>(r)),

  adminLogin: (username: string, password: string): Promise<AdminLoginResponse> =>
    fetch(`${API_BASE}/api/v1/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    }).then((r) => parseJsonResponse<AdminLoginResponse>(r)),

  getDashboardStats: (): Promise<AdminDashboardStats> =>
    fetch(`${API_BASE}/api/v1/admin/dashboard/stats`, {
      headers: getAdminHeaders(),
    }).then((r) => parseJsonResponse<AdminDashboardStats>(r)),

  getLicenseCodes: (): Promise<LicenseCode[]> =>
    fetch(`${API_BASE}/api/v1/admin/license-codes`, {
      headers: getAdminHeaders(),
    }).then((r) => parseJsonResponse<LicenseCode[]>(r)),

  createLicenseCodes: (data: { count: number; max_images?: number; expires_at?: string; note?: string }): Promise<CreateLicenseCodesResponse> =>
    fetch(`${API_BASE}/api/v1/admin/license-codes`, {
      method: 'POST',
      headers: adminJsonHeaders(),
      body: JSON.stringify(data),
    }).then((r) => parseJsonResponse<CreateLicenseCodesResponse>(r)),

  updateLicenseCode: (codeId: string, data: unknown): Promise<Record<string, unknown>> =>
    fetch(`${API_BASE}/api/v1/admin/license-codes/${codeId}`, {
      method: 'PUT',
      headers: adminJsonHeaders(),
      body: JSON.stringify(data),
    }).then((r) => parseJsonResponse<Record<string, unknown>>(r)),

  deleteLicenseCode: (codeId: string): Promise<Record<string, unknown>> =>
    fetch(`${API_BASE}/api/v1/admin/license-codes/${codeId}`, {
      method: 'DELETE',
      headers: getAdminHeaders(),
    }).then((r) => parseJsonResponse<Record<string, unknown>>(r)),

  getPlatformApiSettings: (): Promise<PlatformApiConfig> =>
    fetch(`${API_BASE}/api/v1/admin/settings/platform-api`, {
      headers: getAdminHeaders(),
    }).then((r) => parseJsonResponse<PlatformApiConfig>(r)),

  updatePlatformApiSettings: (data: Omit<PlatformApiConfig, 'configured' | 'source' | 'message'>): Promise<PlatformApiConfig> =>
    fetch(`${API_BASE}/api/v1/admin/settings/platform-api`, {
      method: 'PUT',
      headers: adminJsonHeaders(),
      body: JSON.stringify(data),
    }).then((r) => parseJsonResponse<PlatformApiConfig>(r)),

  getImageUrl: (path: string) =>
    path.startsWith('http') || path.startsWith('data:')
      ? path
      : `${API_BASE}${path}`,

  getDownloadUrl: (path: string) => {
    const filename = path.split('/').pop() || 'image.jpg';
    return `${API_BASE}/api/v1/download/${filename}`;
  },
};
