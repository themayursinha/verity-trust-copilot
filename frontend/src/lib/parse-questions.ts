export function parseQuestions(text: string): string[] {
  if (!text.trim()) return [];

  const lines = text.split("\n");
  const questions: string[] = [];
  let currentQuestion = "";

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      if (currentQuestion) {
        questions.push(currentQuestion.trim());
        currentQuestion = "";
      }
      continue;
    }

    const isNewQuestion =
      /^\d+[.)]\s/.test(line) ||
      /^Q\d+[.:]\s/i.test(line) ||
      /^Question\s*\d+[.:]\s/i.test(line) ||
      /^[•\-*]\s/.test(line) ||
      /^Q:\s/i.test(line) ||
      /^[A-Z][.)]\s/.test(line) ||
      line.endsWith("?") ||
      /^\d+\.\d+\s/.test(line);

    if (isNewQuestion) {
      if (currentQuestion) {
        questions.push(currentQuestion.trim());
      }
      currentQuestion = line.replace(/^\d+[.)]\s*/, "")
        .replace(/^Q\d+[.:]\s*/i, "")
        .replace(/^Question\s*\d+[.:]\s*/i, "")
        .replace(/^[•\-*]\s*/, "")
        .replace(/^Q:\s*/i, "")
        .replace(/^[A-Z][.)]\s*/, "");
    } else if (currentQuestion) {
      currentQuestion += " " + line;
    } else {
      if (line.length > 10 && (line.includes("?") || /^(Do|Does|Is|Are|Can|Will|Has|Have|What|How|When|Where|Who|Why|Which|Please|Describe|Explain|List|Provide|Outline)/i.test(line))) {
        currentQuestion = line;
      }
    }
  }

  if (currentQuestion) {
    questions.push(currentQuestion.trim());
  }

  return questions.filter((q) => q.length > 5);
}
