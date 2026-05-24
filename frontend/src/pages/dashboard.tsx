import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getDashboard, getSoc2Report, downloadAuditPackage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, CheckCircle2, Clock, Download, FileText, Loader2, ShieldCheck, BugPlay, ScrollText, Package } from "lucide-react";

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-20" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {Array.from({ length: 2 }).map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-5 w-32" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-32 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const formatFrameworkId = (id: string) => {
  return id.charAt(0).toUpperCase() + id.slice(1).replace(/-/g, " ");
};

export function DashboardPage() {
  const [exportingReport, setExportingReport] = useState(false);
  const [exportingAudit, setExportingAudit] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
    refetchInterval: 60000,
  });

  const handleExportReport = async () => {
    setExportingReport(true);
    try {
      const reportData = await getSoc2Report();
      const blob = new Blob([reportData.report], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `soc2-report-${new Date().toISOString().split("T")[0]}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
    } finally {
      setExportingReport(false);
    }
  };

  const handleDownloadAudit = async () => {
    setExportingAudit(true);
    try {
      const blob = await downloadAuditPackage();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit-package-${new Date().toISOString().split("T")[0]}.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
    } finally {
      setExportingAudit(false);
    }
  };

  if (isLoading) return <DashboardSkeleton />;

  if (error || !data) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-center">
          <AlertCircle className="mx-auto h-12 w-12 text-destructive" />
          <h3 className="mt-4 text-lg font-semibold">Failed to load dashboard</h3>
          <p className="text-sm text-muted-foreground">
            Could not fetch dashboard data. Please check your connection.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
            <p className="text-sm text-muted-foreground">
              Overview of your security compliance posture
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleExportReport} disabled={exportingReport || exportingAudit}>
              {exportingReport ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Download className="mr-2 h-4 w-4" />
              )}
              {exportingReport ? "Generating..." : "Export SOC 2 Report"}
            </Button>
            <Button variant="outline" onClick={handleDownloadAudit} disabled={exportingAudit || exportingReport}>
              {exportingAudit ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Package className="mr-2 h-4 w-4" />
              )}
              {exportingAudit ? "Packaging..." : "Audit Package"}
            </Button>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Answers</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.approvals.total}</div>
            <div className="flex gap-2 mt-1">
              <Badge variant="secondary" className="text-xs">
                {data.approvals.approved} approved
              </Badge>
              <Badge variant="outline" className="text-xs">
                {data.approvals.unreviewed} pending
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Evidence</CardTitle>
            <ShieldCheck className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.evidence.total}</div>
            <div className="flex gap-2 mt-1">
              <Badge variant="secondary" className="text-xs bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
                {data.evidence.fresh} fresh
              </Badge>
              <Badge variant="secondary" className="text-xs bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300">
                {data.evidence.stale} stale
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Policies</CardTitle>
            <ScrollText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.policies.total}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {data.policies.active} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Frameworks</CardTitle>
            <BugPlay className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.frameworks.length}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {data.evidence.frameworks_covered} covered
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Framework Coverage</CardTitle>
            <CardDescription>
              Compliance coverage across security frameworks
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {data.frameworks.map((fw) => (
              <div key={fw.id} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{formatFrameworkId(fw.id)}</span>
                  <span className="text-muted-foreground">
                    {Math.round(fw.coverage * 100)}%
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary transition-all"
                    style={{ width: `${Math.round(fw.coverage * 100)}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  {fw.evidence_count} evidence across {fw.control_count} controls
                </p>
              </div>
            ))}
            {data.frameworks.length === 0 && (
              <p className="text-sm text-muted-foreground py-4 text-center">
                No framework data available
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Approval Stats</CardTitle>
            <CardDescription>
              Answer approval status breakdown
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                  <span className="text-sm">Approved</span>
                </div>
                <span className="text-sm font-medium">
                  {data.approvals.approved}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  <span className="text-sm">Rejected</span>
                </div>
                <span className="text-sm font-medium">
                  {data.approvals.rejected}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-amber-500" />
                  <span className="text-sm">Unreviewed</span>
                </div>
                <span className="text-sm font-medium">
                  {data.approvals.unreviewed}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Activity</CardTitle>
          <CardDescription>
            Latest actions across your organization
          </CardDescription>
        </CardHeader>
        <CardContent>
          {data.recent_activity.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No recent activity
            </p>
          ) : (
            <div className="space-y-3">
              {data.recent_activity.slice(0, 10).map((activity) => (
                <div
                  key={`${activity.action}-${activity.timestamp}`}
                  className="flex items-start gap-3 border-b pb-3 last:border-0 last:pb-0"
                >
                  <div className="mt-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-muted">
                    <span className="text-xs font-medium">
                      {activity.action.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm">
                      <span className="font-medium">{activity.action}</span>
                      <span className="text-muted-foreground">
                        {" "}
                        &mdash; {activity.detail}
                      </span>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(activity.timestamp)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
