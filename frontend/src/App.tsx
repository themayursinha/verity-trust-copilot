import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "@/hooks/useAuth";
import { AppLayout } from "@/components/app-layout";
import { LoginPage } from "@/pages/login";
import { RegisterPage } from "@/pages/register";
import { DashboardPage } from "@/pages/dashboard";
import { AnswersPage } from "@/pages/answers";
import { EvidencePage } from "@/pages/evidence";
import { PoliciesPage } from "@/pages/policies";
import { PentestsPage } from "@/pages/pentests";
import { SettingsPage } from "@/pages/settings";
import { NotFoundPage } from "@/pages/not-found";
import { LandingPage } from "@/pages/landing";
import TrustCenterAdmin from "@/pages/trust-center-admin";
import PublicTrustCenter from "@/pages/trust-center-public";
import { OnboardingWizard } from "@/components/onboarding-wizard";
import { TooltipProvider } from "@/components/ui/tooltip";
import { type ReactNode, useState, useEffect } from "react";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
});

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="mt-4 text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function HomeRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="mt-4 text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (user) return <Navigate to="/app/dashboard" replace />;

  return <LandingPage />;
}

function ProtectedLayoutWithOnboarding() {
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("onboarding_complete")) {
      setShowOnboarding(true);
    }
  }, []);

  return (
    <>
      <AppLayout />
      <OnboardingWizard
        open={showOnboarding}
        onClose={() => setShowOnboarding(false)}
      />
    </>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <ProtectedLayoutWithOnboarding />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/app/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="answers" element={<AnswersPage />} />
        <Route path="evidence" element={<EvidencePage />} />
        <Route path="policies" element={<PoliciesPage />} />
        <Route path="pentests" element={<PentestsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="trust-center" element={<TrustCenterAdmin />} />
      </Route>
      <Route path="/trust/:orgSlug" element={<PublicTrustCenter />} />
      <Route path="/" element={<HomeRoute />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <TooltipProvider>
          <AuthProvider>
            <AppRoutes />
          </AuthProvider>
        </TooltipProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
