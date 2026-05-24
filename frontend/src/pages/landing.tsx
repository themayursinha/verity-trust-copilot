import { Link } from "react-router-dom";
import { Shield, FileCheck, BarChart3, Users, ArrowRight, Play } from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: Shield,
    title: "BM25-Powered Retrieval",
    description:
      "Matches questions to your evidence library with field-weighted scoring for precise, relevant results.",
  },
  {
    icon: FileCheck,
    title: "Conservative by Design",
    description:
      "Never fabricates claims. Every answer cites verifiable sources from your approved evidence.",
  },
  {
    icon: BarChart3,
    title: "Compliance Dashboard",
    description:
      "Track ISO 27001, SOC 2, GDPR, and DORA coverage at a glance with real-time framework insights.",
  },
  {
    icon: Users,
    title: "Team Collaboration",
    description:
      "Invite your team, manage evidence, review and approve answers together in one place.",
  },
];

export function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
              <Shield className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-lg font-bold">Verity</span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link to="/register">
              <Button>
                Get Started
                <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <section className="relative overflow-hidden bg-gradient-to-br from-green-50 via-teal-50 to-emerald-50 py-20 dark:from-green-950 dark:via-teal-950 dark:to-emerald-950 sm:py-32">
          <div className="absolute inset-0 bg-grid-black/[0.02] dark:bg-grid-white/[0.02]" />
          <div className="absolute left-1/2 top-0 -z-10 h-[600px] w-[600px] -translate-x-1/2 rounded-full bg-gradient-to-br from-primary/20 to-emerald-500/10 blur-3xl dark:from-primary/20 dark:to-emerald-500/10" />
          <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center">
              <div className="mb-8 inline-flex items-center gap-2 rounded-full border bg-background/80 px-4 py-1.5 text-sm shadow-sm">
                <Shield className="h-4 w-4 text-primary" />
                <span className="text-muted-foreground">Self-hosted security compliance</span>
              </div>
              <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
                Automate Security Questionnaires with{" "}
                <span className="bg-gradient-to-r from-primary to-emerald-500 bg-clip-text text-transparent">
                  Trusted AI
                </span>
              </h1>
              <p className="mt-6 text-lg leading-relaxed text-muted-foreground sm:text-xl">
                Stop spending hours answering security questionnaires. Verity Trust
                Copilot uses your approved evidence to generate accurate,
                citation-backed answers in seconds.
              </p>
              <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
                <Link to="/register">
                  <Button size="lg" className="gap-2 text-base">
                    Get Started Free
                    <ArrowRight className="h-5 w-5" />
                  </Button>
                </Link>
                <Link to="/login">
                  <Button variant="outline" size="lg" className="gap-2 text-base">
                    <Play className="h-5 w-5" />
                    View Demo
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="py-20 sm:py-28">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Everything you need to close deals faster
              </h2>
              <p className="mt-4 text-lg text-muted-foreground">
                Built for security teams who need accurate, auditable answers
                without the manual grind.
              </p>
            </div>
            <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="group rounded-xl border bg-card p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-md"
                >
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                    <feature.icon className="h-6 w-6" />
                  </div>
                  <h3 className="mt-5 text-base font-semibold">{feature.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="py-20 sm:py-28">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                See Verity in Action
              </h2>
              <p className="mt-4 text-lg text-muted-foreground">
                Explore the core features that help security teams answer
                questionnaires faster with verifiable, citation-backed results.
              </p>
            </div>
            <div className="mt-16 grid gap-6 sm:grid-cols-2">
              {[
                { label: "Answer Generator", gradient: "from-emerald-500 to-teal-600" },
                { label: "Compliance Dashboard", gradient: "from-teal-500 to-cyan-600" },
                { label: "Evidence Library", gradient: "from-cyan-500 to-blue-600" },
                { label: "Policy Center", gradient: "from-blue-500 to-indigo-600" },
              ].map(({ label, gradient }) => (
                <div key={label} className="space-y-2">
                  <div className={`aspect-video rounded-lg bg-gradient-to-br ${gradient} flex items-center justify-center shadow-sm`}>
                    <span className="text-white/70 text-sm font-medium">Screenshot placeholder</span>
                  </div>
                  <p className="text-center text-sm text-muted-foreground font-medium">{label}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-t bg-muted/30 py-20 sm:py-28">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-3xl text-center">
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
                Self-hosted. Your data stays yours.
              </h2>
              <p className="mt-4 text-lg text-muted-foreground">
                Deploy Verity on your own infrastructure. Per-seat billing with no
                data ever leaving your environment. Built for enterprises that take
                security seriously.
              </p>
              <div className="mt-10">
                <Link to="/register">
                  <Button size="lg" className="gap-2 text-base">
                    Get Started Free
                    <ArrowRight className="h-5 w-5" />
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t bg-background">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 py-8 sm:flex-row sm:px-6 lg:px-8">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Shield className="h-4 w-4" />
            <span>Verity Trust Copilot</span>
          </div>
          <p className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} Verity Trust Copilot. Self-hosted
            security compliance.
          </p>
        </div>
      </footer>
    </div>
  );
}
