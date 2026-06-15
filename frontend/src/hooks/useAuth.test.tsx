import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import * as api from "@/lib/api";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

const mockAuthResponse = {
  access_token: "access_token_123",
  refresh_token: "refresh_token_456",
  token_type: "Bearer",
  user: {
    id: "user-1",
    email: "test@example.com",
    display_name: "Test User",
    role: "admin" as const,
    is_active: true,
    org_id: "org-1",
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  organization: {
    id: "org-1",
    name: "Test Org",
    slug: "test-org",
    brand_color: "#000000",
    logo_url: null,
    max_seats: 5,
    license_key: null,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
};

function createWrapper() {
  const queryClient = new QueryClient();
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <Routes>
            <Route path="/login" element={<div>Login Page</div>} />
            <Route path="/app/dashboard" element={<div>Dashboard Page</div>} />
          </Routes>
          <AuthProvider>{children}</AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );
  };
}

const localStorageMock = {
  data: {} as Record<string, string>,
  getItem: vi.fn((key: string) => localStorageMock.data[key] ?? null),
  setItem: vi.fn((key: string, value: string) => { localStorageMock.data[key] = value; }),
  removeItem: vi.fn((key: string) => { delete localStorageMock.data[key]; }),
  clear: vi.fn(() => { localStorageMock.data = {}; }),
};

Object.defineProperty(window, "localStorage", { value: localStorageMock });

vi.mock("@/lib/api", () => ({
  login: vi.fn(),
  register: vi.fn(),
  refresh: vi.fn(),
  authLogout: vi.fn(),
  default: { post: vi.fn(), get: vi.fn() },
}));

describe("useAuth", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.data = {};
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe("initial state", () => {
    it("loads user from localStorage on mount", () => {
      localStorageMock.data = {
        access_token: "token",
        user: JSON.stringify(mockAuthResponse.user),
        organization: JSON.stringify(mockAuthResponse.organization),
      };

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

      expect(result.current.user).toBeTruthy();
      expect(result.current.user?.email).toBe("test@example.com");
      expect(result.current.organization).toBeTruthy();
      expect(result.current.organization?.name).toBe("Test Org");
    });

    it("starts with no user when localStorage is empty", () => {
      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

      expect(result.current.user).toBeNull();
      expect(result.current.organization).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });

    it("clears auth on JSON parse error in localStorage", () => {
      localStorageMock.data = {
        access_token: "token",
        user: "invalid json",
        organization: JSON.stringify(mockAuthResponse.organization),
      };

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

      expect(result.current.user).toBeNull();
      expect(result.current.organization).toBeNull();
    });
  });

  describe("login", () => {
    it("calls api.login and stores tokens", async () => {
      vi.mocked(api.login).mockResolvedValueOnce(mockAuthResponse);

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

      await act(async () => {
        await result.current.login({ email: "test@example.com", password: "password123" });
      });

      expect(api.login).toHaveBeenCalledWith({ email: "test@example.com", password: "password123" });
      expect(localStorageMock.data["access_token"]).toBe("access_token_123");
      expect(localStorageMock.data["refresh_token"]).toBe("refresh_token_456");
      expect(localStorageMock.data["user"]).toBeTruthy();
      expect(localStorageMock.data["organization"]).toBeTruthy();
    });
  });

  describe("register", () => {
    it("calls api.register and stores tokens", async () => {
      vi.mocked(api.register).mockResolvedValueOnce(mockAuthResponse);

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

      await act(async () => {
        await result.current.register({
          organization_name: "Test Org",
          display_name: "Test User",
          email: "test@example.com",
          password: "password123",
        });
      });

      expect(api.register).toHaveBeenCalledWith({
        organization_name: "Test Org",
        display_name: "Test User",
        email: "test@example.com",
        password: "password123",
      });
      expect(localStorageMock.data["access_token"]).toBe("access_token_123");
    });
  });

  describe("logout", () => {
    it("clears localStorage and resets state", async () => {
      localStorageMock.data = {
        access_token: "token",
        refresh_token: "refresh",
        user: JSON.stringify(mockAuthResponse.user),
        organization: JSON.stringify(mockAuthResponse.organization),
      };
      vi.mocked(api.authLogout).mockResolvedValueOnce(undefined);

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

      await act(async () => {
        await result.current.logout();
      });

      expect(api.authLogout).toHaveBeenCalled();
      expect(result.current.user).toBeNull();
      expect(result.current.organization).toBeNull();
      expect(localStorageMock.data["access_token"]).toBeUndefined();
      expect(localStorageMock.data["refresh_token"]).toBeUndefined();
    });

    it("clears state even if logout API fails", async () => {
      localStorageMock.data = {
        access_token: "token",
        refresh_token: "refresh",
        user: JSON.stringify(mockAuthResponse.user),
        organization: JSON.stringify(mockAuthResponse.organization),
      };
      vi.mocked(api.authLogout).mockRejectedValueOnce(new Error("Network error"));

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

      await act(async () => {
        await result.current.logout();
      });

      expect(result.current.user).toBeNull();
      expect(result.current.organization).toBeNull();
    });
  });

  describe("updateOrganization", () => {
    it("updates organization state and localStorage", () => {
      const updatedOrg = { ...mockAuthResponse.organization, name: "Updated Org", brand_color: "#ff0000" };

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

      act(() => {
        result.current.updateOrganization(updatedOrg);
      });

      expect(result.current.organization?.name).toBe("Updated Org");
      expect(localStorageMock.data["organization"]).toBeTruthy();
    });
  });

  describe("refreshAuth", () => {
    it("refreshes access token and returns true on success", async () => {
      localStorageMock.data = {
        refresh_token: "refresh_token_456",
        user: JSON.stringify(mockAuthResponse.user),
        organization: JSON.stringify(mockAuthResponse.organization),
      };
      vi.mocked(api.refresh).mockResolvedValueOnce({
        access_token: "new_access_token",
        refresh_token: "new_refresh_token",
      });

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.refreshAuth();
      });

      expect(success).toBe(true);
      expect(localStorageMock.data["access_token"]).toBe("new_access_token");
    });

    it("returns false when no refresh token", async () => {
      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.refreshAuth();
      });

      expect(success).toBe(false);
      expect(api.refresh).not.toHaveBeenCalled();
    });

    it("clears auth and returns false when refresh fails", async () => {
      localStorageMock.data = {
        refresh_token: "expired_token",
        user: JSON.stringify(mockAuthResponse.user),
        organization: JSON.stringify(mockAuthResponse.organization),
      };
      vi.mocked(api.refresh).mockRejectedValueOnce(new Error("Token expired"));

      const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });

      let success: boolean | undefined;
      await act(async () => {
        success = await result.current.refreshAuth();
      });

      expect(success).toBe(false);
      expect(result.current.user).toBeNull();
      expect(result.current.organization).toBeNull();
    });
  });

  describe("useAuth throws outside provider", () => {
    it("throws when used outside AuthProvider", () => {
      const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
      expect(() => renderHook(() => useAuth())).toThrow(
        "useAuth must be used within an AuthProvider"
      );
      consoleError.mockRestore();
    });
  });
});