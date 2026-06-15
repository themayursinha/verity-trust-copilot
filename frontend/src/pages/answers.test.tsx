import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AnswersPage } from "@/pages/answers";
import * as api from "@/lib/api";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/app/answers"]}>
          <Routes>
            <Route path="/app/answers" element={children} />
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
  getAnswerGenerations: vi.fn(),
  getLLMStatus: vi.fn(),
  suggestLLMAnswer: vi.fn(),
  generateAnswers: vi.fn(),
  setApproval: vi.fn(),
  exportAnswer: vi.fn(),
  getSampleQuestions: vi.fn(),
  importQuestionsFromFile: vi.fn(),
}));

const mockAnswer = {
  id: "answer-1",
  generation_id: "gen-1",
  question: "What is your encryption standard?",
  answer_text: "We use AES-256 encryption at rest and TLS 1.3 in transit.",
  confidence: "high" as const,
  confidence_rationale: "Based on ISO 27001 certification",
  needs_human_review: false,
  citations: [
    { source_id: "ev-1", title: "ISO 27001 Cert", citation: "Section 5.1", last_reviewed: "2024-01-01" },
  ],
  freshness: [
    { source: "ISO 27001 Cert", status: "fresh" as const, last_reviewed: "2024-01-01", age_days: 30 },
  ],
  created_at: "2024-01-15T00:00:00Z",
};

const mockGeneration = {
  id: "gen-1",
  org_id: "org-1",
  as_of_date: null,
  confidence_counts: { high: 5, medium: 2, low: 1 },
  answers: [mockAnswer],
  created_at: "2024-01-15T00:00:00Z",
};

describe("AnswersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.data = {};
    cleanup();
    vi.mocked(api.getAnswerGenerations).mockResolvedValue([]);
    vi.mocked(api.getLLMStatus).mockResolvedValue({ configured: false, model: null, api_base: null });
  });

  afterEach(() => {
    cleanup();
  });

  it("renders page header", async () => {
    render(<AnswersPage />, { wrapper: createWrapper() });
    expect(screen.getByText("Answers")).toBeTruthy();
  });

  it("renders empty state when no answers", async () => {
    render(<AnswersPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText(/No answers yet/i)).toBeTruthy();
    });
  });

  it("renders answers list when data available", async () => {
    vi.mocked(api.getAnswerGenerations).mockResolvedValue([{ ...mockGeneration }]);
    render(<AnswersPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText("What is your encryption standard?")).toBeTruthy();
    });
  });

  it("has a textarea for questions", async () => {
    render(<AnswersPage />, { wrapper: createWrapper() });
    const textarea = screen.getByPlaceholderText(/Paste your security questions/i);
    expect(textarea).toBeTruthy();
  });

  it("has generate button", async () => {
    render(<AnswersPage />, { wrapper: createWrapper() });
    const buttons = screen.getAllByRole("button");
    const generateBtn = buttons.find(b => b.textContent?.includes("Generate"));
    expect(generateBtn).toBeTruthy();
  });

  it("has load sample button", async () => {
    render(<AnswersPage />, { wrapper: createWrapper() });
    const buttons = screen.getAllByRole("button");
    const sampleBtn = buttons.find(b => b.textContent?.includes("Load Sample"));
    expect(sampleBtn).toBeTruthy();
  });

  it("has import button", async () => {
    render(<AnswersPage />, { wrapper: createWrapper() });
    const buttons = screen.getAllByRole("button");
    const importBtn = buttons.find(b => b.textContent?.includes("Import"));
    expect(importBtn).toBeTruthy();
  });

  it("renders answer card with confidence badge", async () => {
    vi.mocked(api.getAnswerGenerations).mockResolvedValue([{ ...mockGeneration }]);
    render(<AnswersPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      const confidence = screen.getAllByText(/high/i);
      expect(confidence.length).toBeGreaterThan(0);
    });
  });

  it("renders Generate Answers section", async () => {
    render(<AnswersPage />, { wrapper: createWrapper() });
    const cards = screen.queryAllByText("Generate Answers");
    expect(cards.length).toBe(1);
  });
});