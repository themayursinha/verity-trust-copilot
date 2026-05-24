import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  ShieldCheck,
  ScrollText,
  BugPlay,
  Settings,
  LogOut,
  Shield,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

const navItems = [
  { to: "/app/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/app/answers", label: "Answers", icon: FileText },
  { to: "/app/evidence", label: "Evidence", icon: ShieldCheck },
  { to: "/app/policies", label: "Policies", icon: ScrollText },
  { to: "/app/pentests", label: "Pentests", icon: BugPlay },
  { to: "/app/settings", label: "Settings", icon: Settings },
];

export function AppSidebar() {
  const { user, organization, logout } = useAuth();

  return (
    <aside className="flex h-screen w-[260px] flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex items-center gap-3 px-6 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
          <Shield className="h-5 w-5 text-primary-foreground" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight">Verity</h1>
          <p className="text-xs text-sidebar-foreground/60">Trust Copilot</p>
        </div>
      </div>

      <Separator className="mx-4 w-auto bg-sidebar-foreground/10" />

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/20 text-primary-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-foreground/10 hover:text-sidebar-foreground"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <Separator className="mx-4 w-auto bg-sidebar-foreground/10" />

      <div className="p-4">
        <div className="mb-3 space-y-1">
          <p className="text-xs font-medium text-sidebar-foreground/60">
            {organization?.name ?? "Organization"}
          </p>
          <p className="text-sm text-sidebar-foreground/80">
            {user?.display_name ?? "User"}
          </p>
          <p className="text-xs text-sidebar-foreground/50">{user?.email}</p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start gap-2 text-sidebar-foreground/70 hover:bg-sidebar-foreground/10 hover:text-sidebar-foreground"
          onClick={logout}
        >
          <LogOut className="h-4 w-4" />
          Log out
        </Button>
      </div>
    </aside>
  );
}
