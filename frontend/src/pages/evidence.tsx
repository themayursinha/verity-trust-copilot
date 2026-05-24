import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { getEvidence, createEvidence, deleteEvidence } from "@/lib/api";
import type { EvidenceRecord } from "@/types";

function computeFreshness(lastReviewed: string) {
  if (!lastReviewed) return "outdated";
  const days = (Date.now() - new Date(lastReviewed).getTime()) / (1000 * 60 * 60 * 24);
  if (days <= 180) return "fresh";
  if (days <= 365) return "stale";
  return "outdated";
}

function freshnessColor(freshness: string) {
  switch (freshness) {
    case "fresh": return "bg-green-500";
    case "stale": return "bg-amber-500";
    case "outdated": return "bg-red-500";
    default: return "bg-gray-500";
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function EvidencePage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [type, setType] = useState("");
  const [lastReviewed, setLastReviewed] = useState(new Date().toISOString().split("T")[0]);
  const [owner, setOwner] = useState("");
  const [summary, setSummary] = useState("");
  const [snippets, setSnippets] = useState("");
  const queryClient = useQueryClient();

  const { data: evidence, isLoading } = useQuery({
    queryKey: ["evidence"],
    queryFn: getEvidence,
  });

  const createMutation = useMutation({
    mutationFn: (data: Partial<EvidenceRecord>) => createEvidence(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evidence"] });
      setIsDialogOpen(false);
      setTitle("");
      setType("");
      setLastReviewed(new Date().toISOString().split("T")[0]);
      setOwner("");
      setSummary("");
      setSnippets("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteEvidence,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["evidence"] });
    },
  });

  const handleCreate = () => {
    createMutation.mutate({
      title,
      type,
      last_reviewed: lastReviewed,
      owner: owner || "Current User",
      summary: summary || "No summary provided",
      snippets: snippets.split("\n").filter(Boolean),
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Evidence</h2>
          <p className="text-sm text-muted-foreground">
            Manage security evidence and artifacts
          </p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Evidence
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Evidence</DialogTitle>
              <DialogDescription>
                Add a new evidence record to support your security answers
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 max-h-[60vh] overflow-y-auto">
              <div className="space-y-2">
                <Label htmlFor="title">Title *</Label>
                <Input
                  id="title"
                  placeholder="e.g. SOC 2 Type II Report"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="type">Type *</Label>
                <Input
                  id="type"
                  placeholder="e.g. audit_report, policy, certification"
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="owner">Owner</Label>
                  <Input
                    id="owner"
                    placeholder="Security Team"
                    value={owner}
                    onChange={(e) => setOwner(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastReviewed">Last Reviewed *</Label>
                  <Input
                    id="lastReviewed"
                    type="date"
                    value={lastReviewed}
                    onChange={(e) => setLastReviewed(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="summary">Summary *</Label>
                <Input
                  id="summary"
                  placeholder="Brief description of this evidence"
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="snippets">Snippets * (one per line)</Label>
                <textarea
                  id="snippets"
                  className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  placeholder="e.g.&#10;We maintain ISO 27001:2022 certification.&#10;Annual audits are conducted by BSI Group."
                  value={snippets}
                  onChange={(e) => setSnippets(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreate}
                disabled={!title || !type || !lastReviewed || !snippets.trim() || createMutation.isPending}
              >
                {createMutation.isPending ? "Creating..." : "Create"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">All Evidence</CardTitle>
          <CardDescription>
            {evidence?.length ?? 0} records total
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-muted-foreground">Loading...</p>
            </div>
          ) : !evidence || evidence.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12">
              <ShieldCheck className="h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-sm text-muted-foreground">
                No evidence records yet
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Freshness</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-[80px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {evidence.map((record) => {
                  const freshness = computeFreshness(record.last_reviewed);
                  return (
                    <TableRow key={record.id}>
                      <TableCell className="font-medium">
                        {record.title}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{record.type}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span
                            className={`inline-block h-2.5 w-2.5 rounded-full ${freshnessColor(
                              freshness
                            )}`}
                          />
                          <span className="text-sm capitalize">
                            {freshness}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(record.created_at)}
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => deleteMutation.mutate(record.id)}
                          disabled={deleteMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
