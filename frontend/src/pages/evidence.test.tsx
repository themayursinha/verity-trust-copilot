import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { EvidencePage } from "@/pages/evidence";
import * as api from "@/lib/api";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/app/evidence"]}>
          <Routes>
            <Route path="/app/evidence" element={children} />
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
  getEvidence: vi.fn(),
  createEvidence: vi.fn(),
  deleteEvidence: vi.fn(),
}));

const mockEvidence = [
  { id: "ev-1", org_id: "org-1", title: "SOC 2 Report", type: "audit_report", frameworks: ["SOC2"], control_ids: ["CC1"], last_reviewed: "2024-01-01", owner: "admin", summary: "Annual SOC 2 audit", snippets: ["AES-256 encryption"], created_at: "2024-01-01", updated_at: "2024-01-01" },
  { id: "ev-2", org_id: "org-1", title: "ISO Cert", type: "certificate", frameworks: ["ISO27001"], control_ids: ["A.12"], last_reviewed: "2023-06-01", owner: "admin", summary: "ISO 27001", snippets: ["TLS 1.3"], created_at: "2023-06-01", updated_at: "2024-01-01" },
];

describe("EvidencePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.data = {};
    vi.mocked(api.getEvidence).mockResolvedValue([]);
    vi.mocked(api.createEvidence).mockResolvedValue({} as any);
    vi.mocked(api.deleteEvidence).mockResolvedValue(undefined);
  });

  it("renders evidence page header", async () => {
    render(<EvidencePage />, { wrapper: createWrapper() });
    expect(screen.getByRole("heading", { name: /^Evidence$/ })).toBeTruthy();
  });

  it("shows empty state when no evidence", async () => {
    render(<EvidencePage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText(/No evidence records yet/i)).toBeTruthy();
    });
  });

  it("renders evidence list when data available", async () => {
    vi.mocked(api.getEvidence).mockResolvedValue([...mockEvidence]);
    render(<EvidencePage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText("SOC 2 Report")).toBeTruthy();
      expect(screen.getByText("ISO Cert")).toBeTruthy();
    });
  });

  it("shows evidence count in table header", async () => {
    vi.mocked(api.getEvidence).mockResolvedValue([...mockEvidence]);
    const { container } = render(<EvidencePage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(container.textContent?.includes("2 records total")).toBe(true);
    });
  });

  it("renders evidence table with freshness indicators", async () => {
    vi.mocked(api.getEvidence).mockResolvedValue([...mockEvidence]);
    render(<EvidencePage />, { wrapper: createWrapper() });
    await waitFor(() => {
      const fresh = screen.getAllByText(/fresh|stale/i);
      expect(fresh.length).toBeGreaterThan(0);
    });
  });

  it("renders delete button for evidence rows", async () => {
    vi.mocked(api.getEvidence).mockResolvedValue([mockEvidence[0]]);
    render(<EvidencePage />, { wrapper: createWrapper() });
    await waitFor(() => {
      const deleteButtons = screen.getAllByRole("button", { name: "" });
      const trashButton = deleteButtons.find(b => b.innerHTML.includes("trash") || b.querySelector("[data-lucide-trash]"));
      expect(trashButton).toBeTruthy();
    });
  });

  it("shows loading indicator", async () => {
    vi.mocked(api.getEvidence).mockImplementation(() => new Promise(() => {}) as ReturnType<typeof api.getEvidence>);
    const { container } = render(<EvidencePage />, { wrapper: createWrapper() });
    const loading = container.querySelector("text");
    await waitFor(() => {
      expect(container.textContent?.includes("Loading")).toBe(true);
    });
  });
});