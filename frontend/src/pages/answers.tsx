import { useState, useEffect } from "react";
import {
  FileText,
  Sparkles,
  Download,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Loader2,
  AlertTriangle,
  ExternalLink,
  Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { generateAnswers, setApproval, exportAnswer, getSampleQuestions, suggestLLMAnswer, getLLMStatus } from "@/lib/api";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { Answer } from "@/types";

function confidenceColor(confidence: "high" | "medium" | "low" | null) {
  switch (confidence) {
    case "high":
      return "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300";
    case "medium":
      return "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300";
    case "low":
      return "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300";
    default:
      return "bg-muted text-muted-foreground";
  }
}

const EXPORT_FORMATS = ["markdown", "csv", "json"] as const;

export function AnswersPage() {
  const [questions, setQuestions] = useState("");
  const [selectedAnswer, setSelectedAnswer] = useState<Answer | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedAnswers, setGeneratedAnswers] = useState<Answer[]>([]);
  const [loadingSample, setLoadingSample] = useState(false);
  const [llmLoading, setLlmLoading] = useState(false);
  const [llmConfigured, setLlmConfigured] = useState(false);
  const [llmError, setLlmError] = useState<string | null>(null);

  useEffect(() => {
    getLLMStatus().then((s) => setLlmConfigured(s.configured)).catch(() => {});
  }, []);

  const handleLLMSuggest = async () => {
    if (!selectedAnswer) return;
    setLlmLoading(true);
    setLlmError(null);
    try {
      const result = await suggestLLMAnswer(selectedAnswer.question);
      const llmAnswer = {
        id: `llm-${Date.now()}`,
        generation_id: "llm",
        question: result.question,
        answer_text: result.answer_text,
        confidence: "low" as const,
        confidence_rationale: `LLM-generated using ${result.model}. ${result.evidence_used} evidence records as context.`,
        needs_human_review: true,
        citations: [],
        freshness: [],
        created_at: new Date().toISOString(),
        __llm: true as const,
      };
      setGeneratedAnswers((prev) => [llmAnswer as any, ...prev]);
      setSelectedAnswer(llmAnswer as any);
    } catch (e: any) {
      setLlmError(e?.response?.data?.detail || "LLM suggestion failed");
    } finally {
      setLlmLoading(false);
    }
  };

  const handleGenerate = async () => {
    const qs = questions
      .split("\n")
      .map((q) => q.trim())
      .filter(Boolean);
    if (qs.length === 0) return;

    setIsGenerating(true);
    try {
      const result = await generateAnswers(qs);
      setGeneratedAnswers((prev) => [...result.answers, ...prev]);
    } catch {
      // handled by api interceptor
    } finally {
      setIsGenerating(false);
    }
  };

  const handleLoadSample = async () => {
    setLoadingSample(true);
    try {
      const sampleQuestions = await getSampleQuestions();
      setQuestions(sampleQuestions.join("\n"));
    } catch {
      // handled by api interceptor
    } finally {
      setLoadingSample(false);
    }
  };

  const handleApprove = async (answer: Answer) => {
    try {
      await setApproval(answer.question, "approved");
      setSelectedAnswer(null);
      setGeneratedAnswers((prev) =>
        prev.filter((a) => a.id !== answer.id)
      );
    } catch {
      // handled by api interceptor
    }
  };

  const handleReject = async (answer: Answer) => {
    try {
      await setApproval(answer.question, "rejected");
      setSelectedAnswer(null);
      setGeneratedAnswers((prev) =>
        prev.filter((a) => a.id !== answer.id)
      );
    } catch {
      // handled by api interceptor
    }
  };

  const handleExport = async (answer: Answer, format: "markdown" | "csv" | "json") => {
    try {
      const result = await exportAnswer(answer, format);
      if (result.path) {
        window.open(result.path, "_blank");
      }
    } catch {
      // handled by api interceptor
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Answers</h2>
        <p className="text-sm text-muted-foreground">
          Generate and manage security questionnaire answers
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Generate Answers</CardTitle>
          <CardDescription>
            Enter questions (one per line) to generate AI-powered answers
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <textarea
            className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            placeholder="Paste your security questions here, one per line..."
            value={questions}
            onChange={(e) => setQuestions(e.target.value)}
          />
          <div className="flex items-center gap-2">
            <Button
              onClick={handleGenerate}
              disabled={isGenerating || !questions.trim()}
            >
              {isGenerating ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="mr-2 h-4 w-4" />
              )}
              {isGenerating ? "Generating..." : "Generate"}
            </Button>
            <Button
              variant="outline"
              onClick={handleLoadSample}
              disabled={loadingSample}
            >
              {loadingSample ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Load Sample
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-3">
          {generatedAnswers.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <FileText className="h-12 w-12 text-muted-foreground/50" />
                <p className="mt-4 text-sm text-muted-foreground">
                  No answers yet. Generate some above.
                </p>
              </CardContent>
            </Card>
          ) : (
            generatedAnswers.map((answer) => (
              <Card
                key={answer.id}
                className={`cursor-pointer transition-colors hover:border-primary/50 ${
                  selectedAnswer?.id === answer.id ? "border-primary" : ""
                }`}
                onClick={() => setSelectedAnswer(answer)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2 min-w-0">
                      <p className="text-sm font-medium truncate">{answer.question}</p>
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {answer.answer_text}
                      </p>
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge
                          variant="secondary"
                          className={confidenceColor(answer.confidence)}
                        >
                          {answer.confidence ?? "unknown"} confidence
                        </Badge>
                        {answer.needs_human_review && (
                          <Badge
                            variant="secondary"
                            className="bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300"
                          >
                            <AlertTriangle className="mr-1 h-3 w-3" />
                            Needs review
                          </Badge>
                        )}
                        {(answer as any).__llm && (
                          <Badge
                            variant="secondary"
                            className="bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300"
                          >
                            LLM
                          </Badge>
                        )}
                      </div>
                    </div>
                    <ChevronRight className="h-5 w-5 text-muted-foreground shrink-0" />
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        <div className="space-y-4">
          {selectedAnswer ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Answer Detail</CardTitle>
                <CardDescription>{selectedAnswer.question}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-md bg-muted p-4">
                  <p className="text-sm whitespace-pre-wrap">
                    {selectedAnswer.answer_text}
                  </p>
                </div>

                <Separator />

                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Confidence</span>
                  <Badge
                    variant="secondary"
                    className={confidenceColor(selectedAnswer.confidence)}
                  >
                    {selectedAnswer.confidence ?? "unknown"}
                  </Badge>
                </div>

                {selectedAnswer.confidence_rationale && (
                  <div>
                    <span className="text-xs font-medium text-muted-foreground">
                      Confidence Rationale
                    </span>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {selectedAnswer.confidence_rationale}
                    </p>
                  </div>
                )}

                {selectedAnswer.needs_human_review && (
                  <div className="flex items-center gap-2 rounded-md border border-amber-200 bg-amber-50 p-3 dark:border-amber-800 dark:bg-amber-950">
                    <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                    <p className="text-sm text-amber-700 dark:text-amber-300">
                      This answer requires human review before use.
                    </p>
                  </div>
                )}

                {selectedAnswer.citations.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <span className="text-xs font-medium text-muted-foreground">
                        Citations
                      </span>
                      <div className="mt-2 space-y-2">
                        {selectedAnswer.citations.map((c, i) => (
                          <div
                            key={i}
                            className="rounded-md border p-3 text-sm"
                          >
                            <p className="font-medium">{c.title}</p>
                            <p className="mt-1 text-muted-foreground line-clamp-2">
                              {c.citation}
                            </p>
                            <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              Reviewed:{" "}
                              {new Date(c.last_reviewed).toLocaleDateString()}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                {selectedAnswer.freshness.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <span className="text-xs font-medium text-muted-foreground">
                        Source Freshness
                      </span>
                      <div className="mt-2 space-y-2">
                        {selectedAnswer.freshness.map((f, i) => (
                          <div
                            key={i}
                            className="flex items-center justify-between rounded-md border p-3 text-sm"
                          >
                            <span className="font-medium">{f.source}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-muted-foreground">
                                {f.age_days}d ago
                              </span>
                              <Badge
                                variant="secondary"
                                className={
                                  f.status === "fresh"
                                    ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                                    : f.status === "stale"
                                    ? "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300"
                                    : "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
                                }
                              >
                                {f.status}
                              </Badge>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                <Separator />

                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="default"
                    className="flex-1"
                    onClick={() => handleApprove(selectedAnswer)}
                  >
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    className="flex-1"
                    onClick={() => handleReject(selectedAnswer)}
                  >
                    <XCircle className="mr-2 h-4 w-4" />
                    Reject
                  </Button>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" className="w-full">
                      <Download className="mr-2 h-4 w-4" />
                      Export
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    {EXPORT_FORMATS.map((format) => (
                      <DropdownMenuItem
                        key={format}
                        onClick={() => handleExport(selectedAnswer, format)}
                      >
                        <ExternalLink className="mr-2 h-4 w-4" />
                        {format.charAt(0).toUpperCase() + format.slice(1)}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>

                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="w-full">
                      <Button
                        variant="secondary"
                        size="sm"
                        className="w-full"
                        disabled={!llmConfigured || llmLoading}
                        onClick={handleLLMSuggest}
                      >
                        {llmLoading ? (
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        ) : (
                          <Sparkles className="mr-2 h-4 w-4" />
                        )}
                        {llmLoading ? "Generating..." : "AI Suggest"}
                      </Button>
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    {!llmConfigured
                      ? "Set LLM_API_KEY in backend environment to enable AI suggestions"
                      : llmLoading
                      ? "Generating AI suggestion..."
                      : "Generate AI-powered answer suggestion"}
                  </TooltipContent>
                </Tooltip>
                {llmError && (
                  <p className="text-sm text-destructive">{llmError}</p>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <FileText className="h-12 w-12 text-muted-foreground/50" />
                <p className="mt-4 text-sm text-muted-foreground">
                  Select an answer to view details
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
