import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import axios from "axios";
import * as api from "@/lib/api";

vi.mock("axios", () => {
  const mockAxios = vi.fn(() => Promise.resolve({ data: {} })) as unknown as typeof axios;
  (mockAxios as typeof axios & Record<string, unknown>).create = vi.fn(() => mockAxios as never);
  (mockAxios as typeof axios & Record<string, unknown>).post = vi.fn(() => Promise.resolve({ data: {} }));
  (mockAxios as typeof axios & Record<string, unknown>).get = vi.fn(() => Promise.resolve({ data: {} }));
  (mockAxios as typeof axios & Record<string, unknown>).put = vi.fn(() => Promise.resolve({ data: {} }));
  (mockAxios as typeof axios & Record<string, unknown>).delete = vi.fn(() => Promise.resolve({}));
  (mockAxios as typeof axios & Record<string, unknown>).interceptors = {
    request: { use: vi.fn(), eject: vi.fn() },
    response: { use: vi.fn(), eject: vi.fn() },
  };
  return { default: mockAxios, __esModule: true };
});

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");
  return { ...actual };
});

const flushPromises = () => new Promise((r) => setTimeout(r, 0));

describe("API client", () => {
  let mockAxios: typeof axios;

  beforeEach(async () => {
    vi.clearAllMocks();
    vi.resetModules();
    vi.stubGlobal("localStorage", {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
    mockAxios = (await import("@/lib/api")).default;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("login", () => {
    it("posts credentials to login endpoint", async () => {
      const { login } = await import("@/lib/api");
      const mockData = {
        access_token: "token123",
        refresh_token: "refresh123",
        token_type: "Bearer",
        user: { id: "1", email: "test@example.com", display_name: "Test", role: "admin", is_active: true, org_id: "org1", created_at: "", updated_at: "" },
        organization: { id: "org1", name: "Test Org", slug: "test-org", brand_color: "#000000", logo_url: null, max_seats: 5, license_key: null, created_at: "", updated_at: "" },
      };
      vi.mocked(axios.post).mockResolvedValueOnce({ data: mockData });

      const result = await login({
        email: "test@example.com",
        password: "password123",
      });

      expect(axios.post).toHaveBeenCalledWith(
        "/api/v1/auth/login",
        { email: "test@example.com", password: "password123" }
      );
      expect(result).toEqual(mockData);
    });
  });

  describe("register", () => {
    it("posts registration data to register endpoint", async () => {
      const { register } = await import("@/lib/api");
      const mockData = {
        access_token: "token123",
        refresh_token: "refresh123",
        token_type: "Bearer",
        user: { id: "1", email: "test@example.com", display_name: "Test", role: "admin", is_active: true, org_id: "org1", created_at: "", updated_at: "" },
        organization: { id: "org1", name: "Test Org", slug: "test-org", brand_color: "#000000", logo_url: null, max_seats: 5, license_key: null, created_at: "", updated_at: "" },
      };
      vi.mocked(axios.post).mockResolvedValueOnce({ data: mockData });

      const result = await register({
        organization_name: "Test Org",
        display_name: "Test User",
        email: "test@example.com",
        password: "password123",
      });

      expect(axios.post).toHaveBeenCalledWith(
        "/api/v1/auth/register",
        { organization_name: "Test Org", display_name: "Test User", email: "test@example.com", password: "password123" }
      );
      expect(result).toEqual(mockData);
    });
  });

  describe("getDashboard", () => {
    it("fetches dashboard data from correct endpoint", async () => {
      const { getDashboard } = await import("@/lib/api");
      const mockDashboard = {
        frameworks: [{ id: "SOC2", coverage: 80, evidence_count: 10, control_count: 5 }],
        evidence: { total: 20, fresh: 15, stale: 3, frameworks_covered: 4 },
        policies: { total: 5, active: 3, draft: 2, upcoming_reviews: 1 },
        approvals: { total: 10, approved: 7, rejected: 1, unreviewed: 2 },
        recent_activity: [],
      };
      vi.mocked(axios.get).mockResolvedValueOnce({ data: mockDashboard });

      const result = await getDashboard();

      expect(axios.get).toHaveBeenCalledWith("/api/v1/dashboard/overview");
      expect(result).toEqual(mockDashboard);
    });
  });

  describe("getEvidence", () => {
    it("fetches evidence records", async () => {
      const { getEvidence } = await import("@/lib/api");
      const mockEvidence = [
        { id: "1", org_id: "org1", title: "ISO Cert", type: "certificate", frameworks: ["ISO27001"], control_ids: ["A.12"], last_reviewed: "2024-01-01", owner: "admin", summary: "Summary", snippets: [], created_at: "", updated_at: "" },
      ];
      vi.mocked(axios.get).mockResolvedValueOnce({ data: mockEvidence });

      const result = await getEvidence();

      expect(axios.get).toHaveBeenCalledWith("/api/v1/evidence");
      expect(result).toEqual(mockEvidence);
    });
  });

  describe("createEvidence", () => {
    it("posts evidence data to create endpoint", async () => {
      const { createEvidence } = await import("@/lib/api");
      const mockEvidence = { id: "new1", title: "New Evidence" };
      vi.mocked(axios.post).mockResolvedValueOnce({ data: mockEvidence });

      const result = await createEvidence({ title: "New Evidence", type: "document" });

      expect(axios.post).toHaveBeenCalledWith(
        "/api/v1/evidence",
        { title: "New Evidence", type: "document" }
      );
      expect(result).toEqual(mockEvidence);
    });
  });

  describe("deleteEvidence", () => {
    it("deletes evidence by ID", async () => {
      const { deleteEvidence } = await import("@/lib/api");
      vi.mocked(axios.delete).mockResolvedValueOnce({});

      await deleteEvidence("evidence-123");

      expect(axios.delete).toHaveBeenCalledWith("/api/v1/evidence/evidence-123");
    });
  });

  describe("getPolicies", () => {
    it("fetches all policies", async () => {
      const { getPolicies } = await import("@/lib/api");
      const mockPolicies = [
        { id: "1", org_id: "org1", title: "Security Policy", category: "security", content: "Content", status: "active", version: 1, review_interval_months: 12, next_review: "2025-01-01", created_at: "", updated_at: "" },
      ];
      vi.mocked(axios.get).mockResolvedValueOnce({ data: mockPolicies });

      const result = await getPolicies();

      expect(axios.get).toHaveBeenCalledWith("/api/v1/policies");
      expect(result).toEqual(mockPolicies);
    });
  });

  describe("createPolicy", () => {
    it("posts policy data to create endpoint", async () => {
      const { createPolicy } = await import("@/lib/api");
      const mockPolicy = { id: "new1", title: "New Policy" };
      vi.mocked(axios.post).mockResolvedValueOnce({ data: mockPolicy });

      const result = await createPolicy({ title: "New Policy", category: "security", content: "Content" });

      expect(axios.post).toHaveBeenCalledWith(
        "/api/v1/policies",
        { title: "New Policy", category: "security", content: "Content" }
      );
      expect(result).toEqual(mockPolicy);
    });
  });

  describe("getPentests", () => {
    it("fetches pentests", async () => {
      const { getPentests } = await import("@/lib/api");
      const mockPentests = [
        { id: "1", org_id: "org1", title: "Annual Pentest", scope: "All systems", methodology: "Black box", start_date: null, end_date: null, status: "planned", findings: [], created_at: "", updated_at: "" },
      ];
      vi.mocked(axios.get).mockResolvedValueOnce({ data: mockPentests });

      const result = await getPentests();

      expect(axios.get).toHaveBeenCalledWith("/api/v1/pentests");
      expect(result).toEqual(mockPentests);
    });
  });

  describe("getLLMStatus", () => {
    it("fetches LLM status", async () => {
      const { getLLMStatus } = await import("@/lib/api");
      vi.mocked(axios.get).mockResolvedValueOnce({ data: { configured: true, model: "gpt-4", api_base: null } });

      const result = await getLLMStatus();

      expect(axios.get).toHaveBeenCalledWith("/api/v1/llm/status");
      expect(result.configured).toBe(true);
      expect(result.model).toBe("gpt-4");
    });
  });

  describe("getLicenseStatus", () => {
    it("fetches license status", async () => {
      const { getLicenseStatus } = await import("@/lib/api");
      vi.mocked(axios.get).mockResolvedValueOnce({ data: { status: "active", max_seats: 10, valid: true } });

      const result = await getLicenseStatus();

      expect(axios.get).toHaveBeenCalledWith("/api/v1/org/license");
      expect(result.status).toBe("active");
    });
  });

  describe("activateLicense", () => {
    it("posts license key to activate endpoint", async () => {
      const { activateLicense } = await import("@/lib/api");
      vi.mocked(axios.post).mockResolvedValueOnce({ data: { status: "active", max_seats: 10 } });

      const result = await activateLicense("LICENSE-KEY-123");

      expect(axios.post).toHaveBeenCalledWith("/api/v1/org/license/activate", { license_key: "LICENSE-KEY-123" });
      expect(result.status).toBe("active");
    });
  });

  describe("updateBranding", () => {
    it("updates org branding", async () => {
      const { updateBranding } = await import("@/lib/api");
      vi.mocked(axios.put).mockResolvedValueOnce({ data: { brand_color: "#00ff00", logo_url: "https://example.com/logo.png" } });

      const result = await updateBranding({ brand_color: "#00ff00", logo_url: "https://example.com/logo.png" });

      expect(axios.put).toHaveBeenCalledWith("/api/v1/org/branding", { brand_color: "#00ff00", logo_url: "https://example.com/logo.png" });
      expect(result.brand_color).toBe("#00ff00");
    });
  });
});