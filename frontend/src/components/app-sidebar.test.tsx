import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { AppSidebar } from "@/components/app-sidebar";
import { AppLayout } from "@/components/app-layout";

const localStorageMock = {
  data: {} as Record<string, string>,
  getItem: vi.fn((key: string) => localStorageMock.data[key] ?? null),
  setItem: vi.fn((key: string, value: string) => { localStorageMock.data[key] = value; }),
  removeItem: vi.fn((key: string) => { delete localStorageMock.data[key]; }),
  clear: vi.fn(() => { localStorageMock.data = {}; }),
};
Object.defineProperty(window, "localStorage", { value: localStorageMock });

const mockUser = {
  id: "user-1",
  email: "test@example.com",
  display_name: "Test User",
  role: "admin" as const,
  is_active: true,
  org_id: "org-1",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockOrg = {
  id: "org-1",
  name: "Test Org",
  slug: "test-org",
  brand_color: "#000000",
  logo_url: null,
  max_seats: 5,
  license_key: null,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

function createSidebarWrapper() {
  const queryClient = new QueryClient();
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <Routes>
            <Route path="/app/dashboard" element={<div>Dashboard</div>} />
            <Route path="/app/answers" element={<div>Answers</div>} />
          </Routes>
          {children}
        </MemoryRouter>
      </QueryClientProvider>
    );
  };
}

const mockLogout = vi.fn();

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    user: mockUser,
    organization: mockOrg,
    logout: mockLogout,
  }),
}));

vi.mock("@/lib/utils", () => ({
  cn: (...args: (string | boolean | undefined | null)[]) => args.filter(Boolean).join(" "),
}));

describe("AppSidebar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.data = {};
    cleanup();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders sidebar with brand name", async () => {
    render(<AppSidebar />, { wrapper: createSidebarWrapper() });
    expect(screen.getByText("Verity")).toBeTruthy();
    expect(screen.getByText("Trust Copilot")).toBeTruthy();
  });

  it("displays organization name", async () => {
    render(<AppSidebar />, { wrapper: createSidebarWrapper() });
    expect(screen.getByText("Test Org")).toBeTruthy();
  });

  it("displays user display name and email", async () => {
    render(<AppSidebar />, { wrapper: createSidebarWrapper() });
    expect(screen.getByText("Test User")).toBeTruthy();
    expect(screen.getByText("test@example.com")).toBeTruthy();
  });

  it("renders navigation items", async () => {
    render(<AppSidebar />, { wrapper: createSidebarWrapper() });
    expect(screen.getByText("Dashboard")).toBeTruthy();
    expect(screen.getByText("Answers")).toBeTruthy();
    expect(screen.getByText("Evidence")).toBeTruthy();
    expect(screen.getByText("Policies")).toBeTruthy();
    expect(screen.getByText("Pentests")).toBeTruthy();
    expect(screen.getByText("Settings")).toBeTruthy();
  });

  it("renders logo fallback when no logo_url", async () => {
    render(<AppSidebar />, { wrapper: createSidebarWrapper() });
    const logoContainer = document.querySelector('[class*="rounded-lg"]');
    expect(logoContainer).toBeTruthy();
  });

  it("renders logout button", async () => {
    render(<AppSidebar />, { wrapper: createSidebarWrapper() });
    expect(screen.getByText("Log out")).toBeTruthy();
  });

  it("calls logout when logout button is clicked", async () => {
    render(<AppSidebar />, { wrapper: createSidebarWrapper() });
    await waitFor(() => {
      fireEvent.click(screen.getByText("Log out"));
    });
    expect(mockLogout).toHaveBeenCalled();
  });

  it("renders nav links with correct href", async () => {
    render(<AppSidebar />, { wrapper: createSidebarWrapper() });
    const links = document.querySelectorAll('a[href="/app/dashboard"], a[href="/app/answers"], a[href="/app/evidence"]');
    expect(links.length).toBeGreaterThan(0);
  });
});

describe("AppLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    cleanup();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders layout with sidebar and header", async () => {
    render(
      <MemoryRouter initialEntries={["/app/dashboard"]}>
        <AppLayout />
      </MemoryRouter>
    );
    const headings = screen.getAllByText("Dashboard");
    expect(headings.length).toBeGreaterThan(0);
  });

  it("renders breadcrumb based on current route", async () => {
    render(
      <MemoryRouter initialEntries={["/app/answers"]}>
        <AppLayout />
      </MemoryRouter>
    );
    const headings = screen.getAllByText("Answers");
    expect(headings.length).toBeGreaterThan(0);
  });

  it("renders Outlet for nested routes", async () => {
    render(
      <MemoryRouter initialEntries={["/app/evidence"]}>
        <AppLayout />
      </MemoryRouter>
    );
    const text = document.body.textContent || "";
    expect(text.includes("Evidence")).toBe(true);
  });

  it("shows page name in header", async () => {
    render(
      <MemoryRouter initialEntries={["/app/policies"]}>
        <AppLayout />
      </MemoryRouter>
    );
    const text = document.body.textContent || "";
    expect(text.includes("Policies")).toBe(true);
  });
});