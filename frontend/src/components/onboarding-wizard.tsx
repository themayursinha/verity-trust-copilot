import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Upload,
  FileText,
  Users,
  PartyPopper,
  ChevronLeft,
  ChevronRight,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

interface OnboardingWizardProps {
  open: boolean;
  onClose: () => void;
}

interface Step {
  icon: typeof Upload;
  title: string;
  description: string;
  actionLabel: string;
  actionPath: string;
}

const steps: Step[] = [
  {
    icon: Upload,
    title: "Upload Evidence",
    description:
      "Start by uploading your security documents, certificates, policies, and compliance reports. Verity uses this evidence library to generate accurate, citation-backed answers to every questionnaire you receive. The more evidence you provide, the more questions Verity can answer automatically.",
    actionLabel: "Go to Evidence",
    actionPath: "/app/evidence",
  },
  {
    icon: FileText,
    title: "Try Sample Questions",
    description:
      "Once you have evidence in place, paste a security questionnaire and watch Verity generate answers with inline citations back to your documents. Each answer is conservative by design — Verity never fabricates claims, and every response links to specific passages in your approved evidence.",
    actionLabel: "Try Answers",
    actionPath: "/app/answers",
  },
  {
    icon: Users,
    title: "Invite Your Team",
    description:
      "Security compliance is a team effort. Invite your colleagues to collaborate — they can upload evidence, review AI-generated answers, approve responses, and help maintain your organization's compliance posture across all frameworks.",
    actionLabel: "Go to Settings",
    actionPath: "/app/settings",
  },
  {
    icon: PartyPopper,
    title: "You're Ready!",
    description:
      "Your organization is set up with evidence management, AI-powered answer generation, and team collaboration. You can always return to upload more evidence, review answers, or manage your team from the dashboard. Congratulations on taking control of your security compliance workflow.",
    actionLabel: "Go to Dashboard",
    actionPath: "/app/dashboard",
  },
];

export function OnboardingWizard({ open, onClose }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const navigate = useNavigate();

  const handleFinish = () => {
    localStorage.setItem("onboarding_complete", "true");
    onClose();
  };

  const handleSkip = () => {
    localStorage.setItem("onboarding_complete", "true");
    onClose();
  };

  const handleAction = () => {
    const step = steps[currentStep];
    if (currentStep === steps.length - 1) {
      handleFinish();
    } else {
      setCurrentStep((prev) => prev + 1);
    }
    navigate(step.actionPath);
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const step = steps[currentStep];
  const StepIcon = step.icon;
  const isLast = currentStep === steps.length - 1;

  return (
    <Dialog open={open} onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-center text-xl">Welcome to Verity</DialogTitle>
          <DialogDescription className="text-center">
            Let&apos;s get you set up in just a few steps
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-center justify-center gap-1.5 py-2">
          {steps.map((_, i) => (
            <div
              key={i}
              className={`h-2 rounded-full transition-all duration-300 ${
                i === currentStep
                  ? "w-8 bg-primary"
                  : i < currentStep
                    ? "w-2 bg-primary/60"
                    : "w-2 bg-muted-foreground/25"
              }`}
            />
          ))}
        </div>

        <div className="flex flex-col items-center py-6 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <StepIcon className="h-8 w-8" />
          </div>
          <h3 className="mt-5 text-lg font-semibold">{step.title}</h3>
          <p className="mt-3 max-w-sm text-sm leading-relaxed text-muted-foreground">
            {step.description}
          </p>
        </div>

        <div className="flex items-center justify-between gap-3">
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handlePrev}
              disabled={currentStep === 0}
            >
              <ChevronLeft className="h-4 w-4" />
              Back
            </Button>
            {!isLast && (
              <Button variant="ghost" size="sm" onClick={handleSkip}>
                Skip
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            {isLast ? (
              <Button onClick={handleFinish} className="gap-2">
                <Check className="h-4 w-4" />
                Finish
              </Button>
            ) : (
              <>
                <Button variant="outline" onClick={handleAction} className="gap-2">
                  {step.actionLabel}
                </Button>
                <Button onClick={handleNext} className="gap-2">
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
