import axios from "axios";
import type {
  AuthResponse,
  LoginRequest,
  RegisterRequest,
  DashboardData,
  AnswerGeneration,
  Answer,
  EvidenceRecord,
  Policy,
  Pentest,
  Finding,
  User,
} from "@/types";

const api = axios.create({
  baseURL: "",
  headers: { "Content-Type": "application/json" },
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem("refresh_token");
      if (!refreshToken) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        localStorage.removeItem("organization");
        isRefreshing = false;
        window.location.href = "/login";
        return Promise.reject(error);
      }

      try {
        const response = await axios.post<{ access_token: string; refresh_token: string }>(
          "/api/v1/auth/refresh",
          { refresh_token: refreshToken }
        );
        const newAccessToken = response.data.access_token;
        const newRefreshToken = response.data.refresh_token;
        localStorage.setItem("access_token", newAccessToken);
        localStorage.setItem("refresh_token", newRefreshToken);
        processQueue(null, newAccessToken);
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        localStorage.removeItem("organization");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export async function login(data: LoginRequest): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>("/api/v1/auth/login", data);
  return response.data;
}

export async function register(data: RegisterRequest): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>("/api/v1/auth/register", data);
  return response.data;
}

export async function refresh(
  refreshToken: string
): Promise<{ access_token: string; refresh_token: string }> {
  const response = await axios.post<{ access_token: string; refresh_token: string }>(
    "/api/v1/auth/refresh",
    { refresh_token: refreshToken }
  );
  return response.data;
}

export async function authLogout(): Promise<void> {
  await api.post("/api/v1/auth/logout");
}

export async function getOrgMembers(): Promise<User[]> {
  const response = await api.get<User[]>("/api/v1/org/members");
  return response.data;
}

export async function inviteMember(email: string, role: string = "member"): Promise<User> {
  const response = await api.post<User>("/api/v1/org/members/invite", { email, role });
  return response.data;
}

export async function updateMember(userId: string, data: { role?: string; is_active?: boolean }): Promise<User> {
  const response = await api.put<User>(`/api/v1/org/members/${userId}`, data);
  return response.data;
}

export async function removeMember(userId: string): Promise<void> {
  await api.delete(`/api/v1/org/members/${userId}`);
}

export async function getOrgInfo(): Promise<{
  id: string;
  name: string;
  slug: string;
  max_seats: number;
  seats_used: number;
  license_key: string | null;
  created_at: string | null;
}> {
  const response = await api.get("/api/v1/org/me");
  return response.data;
}

export async function getDashboard(): Promise<DashboardData> {
  const response = await api.get<DashboardData>("/api/v1/dashboard/overview");
  return response.data;
}

export async function getEvidence(): Promise<EvidenceRecord[]> {
  const response = await api.get<EvidenceRecord[]>("/api/v1/evidence");
  return response.data;
}

export async function createEvidence(data: Partial<EvidenceRecord>): Promise<EvidenceRecord> {
  const response = await api.post<EvidenceRecord>("/api/v1/evidence", data);
  return response.data;
}

export async function deleteEvidence(id: string): Promise<void> {
  await api.delete(`/api/v1/evidence/${id}`);
}

export async function getSampleQuestions(): Promise<string[]> {
  const response = await api.get<string[]>("/api/v1/sample");
  return response.data;
}

export async function generateAnswers(questions: string[], asOf?: string): Promise<AnswerGeneration> {
  const response = await api.post<AnswerGeneration>("/api/v1/answers", {
    questions,
    as_of: asOf,
  });
  return response.data;
}

export async function setApproval(
  question: string,
  status: "approved" | "rejected" | "unreviewed",
  notes?: string
): Promise<void> {
  await api.post("/api/v1/approval", { question, status, notes });
}

export async function exportAnswer(
  answer: Answer,
  format: "markdown" | "csv" | "json"
): Promise<{ path: string; markdown?: string; csv?: string; json?: string }> {
  const endpoint = format === "csv" ? "/api/v1/export/csv" : format === "json" ? "/api/v1/export/json" : "/api/v1/export";
  const response = await api.post(endpoint, { answer });
  return response.data;
}

export async function getPolicies(): Promise<Policy[]> {
  const response = await api.get<Policy[]>("/api/v1/policies");
  return response.data;
}

export async function createPolicy(data: Partial<Policy>): Promise<Policy> {
  const response = await api.post<Policy>("/api/v1/policies", data);
  return response.data;
}

export async function updatePolicy(id: string, data: Partial<Policy>): Promise<Policy> {
  const response = await api.put<Policy>(`/api/v1/policies/${id}`, data);
  return response.data;
}

export async function deletePolicy(id: string): Promise<void> {
  await api.delete(`/api/v1/policies/${id}`);
}

export async function getPentests(): Promise<Pentest[]> {
  const response = await api.get<Pentest[]>("/api/v1/pentests");
  return response.data;
}

export async function createPentest(data: Partial<Pentest>): Promise<Pentest> {
  const response = await api.post<Pentest>("/api/v1/pentests", data);
  return response.data;
}

export async function updatePentest(id: string, data: Partial<Pentest>): Promise<Pentest> {
  const response = await api.put<Pentest>(`/api/v1/pentests/${id}`, data);
  return response.data;
}

export async function deletePentest(id: string): Promise<void> {
  await api.delete(`/api/v1/pentests/${id}`);
}

export async function addFinding(pentestId: string, data: Partial<Finding>): Promise<Finding> {
  const response = await api.post<Finding>(`/api/v1/pentests/${pentestId}/findings`, data);
  return response.data;
}

export async function deleteFinding(pentestId: string, findingId: string): Promise<void> {
  await api.delete(`/api/v1/pentests/${pentestId}/findings/${findingId}`);
}

export async function getLLMStatus(): Promise<{ configured: boolean; model: string | null; api_base: string | null }> {
  const response = await api.get("/api/v1/llm/status");
  return response.data;
}

export async function suggestLLMAnswer(question: string): Promise<{
  question: string;
  answer_text: string;
  model: string;
  usage: { prompt_tokens: number; completion_tokens: number };
  evidence_used: number;
  needs_human_review: boolean;
  source: string;
}> {
  const response = await api.post("/api/v1/llm/suggest", { question });
  return response.data;
}

export async function getLicenseStatus(): Promise<{
  status: string;
  max_seats: number;
  org_name?: string;
  customer_email?: string;
  expires_at?: number;
  reason?: string;
  valid?: boolean;
}> {
  const response = await api.get("/api/v1/org/license");
  return response.data;
}

export async function activateLicense(licenseKey: string): Promise<{
  status: string;
  max_seats: number;
  org_name?: string;
}> {
  const response = await api.post("/api/v1/org/license/activate", { license_key: licenseKey });
  return response.data;
}

export { type AuthResponse };
export default api;
