import { Outlet, useLocation } from "react-router-dom";
import { AppSidebar } from "@/components/app-sidebar";
import { Toaster } from "@/components/ui/toast";

const breadcrumbMap: Record<string, string> = {
  "/app/dashboard": "Dashboard",
  "/app/answers": "Answers",
  "/app/evidence": "Evidence",
  "/app/policies": "Policies",
  "/app/pentests": "Pentests",
  "/app/settings": "Settings",
};

export function AppLayout() {
  const location = useLocation();
  const currentPage = breadcrumbMap[location.pathname] ?? "Page";

  return (
    <div className="flex h-screen overflow-hidden">
      <AppSidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-14 items-center gap-4 border-b bg-background px-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="font-medium text-foreground">{currentPage}</span>
          </div>
          <div className="ml-auto flex items-center gap-2" />
        </header>
        <div className="flex-1 overflow-auto p-6">
          <Outlet />
        </div>
      </main>
      <Toaster />
    </div>
  );
}
