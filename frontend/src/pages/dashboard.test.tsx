import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { DashboardPage } from "@/pages/dashboard";
import * as api from "@/lib/api";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/app/dashboard"]}>
          <Routes>
            <Route path="/app/dashboard" element={children} />
          </Routes>
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
  getDashboard: vi.fn(),
  getSoc2Report: vi.fn(),
  downloadAuditPackage: vi.fn(),
}));

const mockDashboard = {
  frameworks: [
    { id: "SOC2", coverage: 0.75, evidence_count: 10, control_count: 5 },
    { id: "ISO27001", coverage: 0.5, evidence_count: 5, control_count: 3 },
  ],
  evidence: { total: 15, fresh: 10, stale: 3, frameworks_covered: 4 },
  policies: { total: 5, active: 3, draft: 2, upcoming_reviews: 1 },
  approvals: { total: 20, approved: 12, rejected: 2, unreviewed: 6 },
  recent_activity: [
    { action: "Created", detail: "SOC 2 Report evidence", timestamp: "2024-01-15T10:00:00Z" },
    { action: "Approved", detail: "Encryption question", timestamp: "2024-01-14T15:00:00Z" },
  ],
};

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.data = {};
    cleanup();
    vi.mocked(api.getDashboard).mockResolvedValue({ ...mockDashboard });
    vi.mocked(api.getSoc2Report).mockResolvedValue({ format: "markdown", report: "# SOC 2 Report", generated_at: "2024-01-15T00:00:00Z", stats: { evidence: 10, policies: 5, pentests: 2, answers: 20, approved_answers: 12, needs_review: 6 } });
    vi.mocked(api.downloadAuditPackage).mockResolvedValue(new Blob());
  });

  afterEach(() => {
    cleanup();
  });

  it("renders dashboard heading", async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeTruthy();
    });
  });

  it("renders metric cards with data", async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      const headings = screen.getAllByRole("heading");
      const dashboardHeading = headings.find(h => h.textContent === "Dashboard");
      expect(dashboardHeading).toBeTruthy();
      expect(screen.getByText("Evidence")).toBeTruthy();
      expect(screen.getByText("Policies")).toBeTruthy();
      expect(screen.getByText("Frameworks")).toBeTruthy();
    });
  });

  it("displays numeric metric values", async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText("20")).toBeTruthy();
      expect(screen.getByText("15")).toBeTruthy();
    });
  });

  it("renders framework coverage section", async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      const sections = screen.getAllByText("Framework Coverage");
      expect(sections.length).toBe(1);
    });
  });

  it("renders approval stats section", async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      const sections = screen.getAllByText("Approval Stats");
      expect(sections.length).toBe(1);
    });
  });

  it("renders recent activity section", async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      const sections = screen.getAllByText("Recent Activity");
      expect(sections.length).toBe(1);
    });
  });

  it("shows error state when data fetch fails", async () => {
    vi.mocked(api.getDashboard).mockRejectedValueOnce(new Error("Network error"));
    render(<DashboardPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText("Failed to load dashboard")).toBeTruthy();
    });
  });

  it("renders skeleton on initial load", async () => {
    vi.mocked(api.getDashboard).mockImplementation(() => new Promise(() => {}) as ReturnType<typeof api.getDashboard>);
    const { container } = render(<DashboardPage />, { wrapper: createWrapper() });
    const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });
});