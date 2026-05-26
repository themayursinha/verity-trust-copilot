import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Globe,
  Bot,
  Bell,
  FileText,
  BarChart3,
  Users,
  Plus,
  Trash2,
  Save,
  ToggleLeft,
  ToggleRight,
  Download,
  Shield,
  Copy,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import api from "@/lib/api";

function TrustCenterPage() {
  const queryClient = useQueryClient();
  const [docDialogOpen, setDocDialogOpen] = useState(false);
  const [docTitle, setDocTitle] = useState("");
  const [docDescription, setDocDescription] = useState("");
  const [docNda, setDocNda] = useState(false);
  const [docPublic, setDocPublic] = useState(false);
  const [copiedUrl, setCopiedUrl] = useState(false);

  const { data: settings, isLoading: settingsLoading } = useQuery({
    queryKey: ["trust-center-settings"],
    queryFn: async () => {
      const resp = await api.get("/api/v1/trust-center/settings");
      return resp.data;
    },
  });

  const { data: documents, isLoading: docsLoading } = useQuery({
    queryKey: ["trust-center-documents"],
    queryFn: async () => {
      const resp = await api.get("/api/v1/trust-center/documents");
      return resp.data;
    },
  });

  const { data: analytics } = useQuery({
    queryKey: ["trust-center-analytics"],
    queryFn: async () => {
      const resp = await api.get("/api/v1/trust-center/analytics");
      return resp.data;
    },
    refetchInterval: 30000,
  });

  const { data: subscribers } = useQuery({
    queryKey: ["trust-center-subscribers"],
    queryFn: async () => {
      const resp = await api.get("/api/v1/trust-center/subscribers");
      return resp.data;
    },
  });

  const { data: accessRequests } = useQuery({
    queryKey: ["trust-center-access-requests"],
    queryFn: async () => {
      const resp = await api.get("/api/v1/trust-center/access-requests");
      return resp.data;
    },
  });

  const updateSettingsMutation = useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const resp = await api.put("/api/v1/trust-center/settings", data);
      return resp.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trust-center-settings"] });
    },
  });

  const createDocMutation = useMutation({
    mutationFn: async (data: Record<string, unknown>) => {
      const resp = await api.post("/api/v1/trust-center/documents", data);
      return resp.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trust-center-documents"] });
      setDocDialogOpen(false);
      setDocTitle("");
      setDocDescription("");
    },
  });

  const deleteDocMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/v1/trust-center/documents/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trust-center-documents"] });
    },
  });

  const approveRequestMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      await api.put(`/api/v1/trust-center/access-requests/${id}`, { status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trust-center-access-requests"] });
    },
  });

  const trustCenterUrl = `${window.location.origin}/trust/YOUR_ORG_SLUG`;

  const handleToggle = (key: string, value: boolean) => {
    updateSettingsMutation.mutate({ [key]: value });
  };

  const handleSaveSettings = () => {
    queryClient.invalidateQueries({ queryKey: ["trust-center-settings"] });
  };

  if (settingsLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Trust Center</h1>
          <p className="text-sm text-muted-foreground">
            Public-facing trust portal for prospects and customers.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => { navigator.clipboard.writeText(trustCenterUrl); setCopiedUrl(true); setTimeout(() => setCopiedUrl(false), 2000); }}>
            {copiedUrl ? <Check className="mr-2 h-4 w-4" /> : <Copy className="mr-2 h-4 w-4" />}
            Copy URL
          </Button>
          <Button
            variant={settings?.enabled ? "default" : "outline"}
            onClick={() => handleToggle("enabled", !settings?.enabled)}
          >
            {settings?.enabled ? <ToggleRight className="mr-2 h-4 w-4" /> : <ToggleLeft className="mr-2 h-4 w-4" />}
            {settings?.enabled ? "Enabled" : "Disabled"}
          </Button>
        </div>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview"><Globe className="mr-2 h-4 w-4" />Overview</TabsTrigger>
          <TabsTrigger value="branding"><Shield className="mr-2 h-4 w-4" />Branding</TabsTrigger>
          <TabsTrigger value="documents"><FileText className="mr-2 h-4 w-4" />Documents</TabsTrigger>
          <TabsTrigger value="requests"><Users className="mr-2 h-4 w-4" />Access Requests</TabsTrigger>
          <TabsTrigger value="analytics"><BarChart3 className="mr-2 h-4 w-4" />Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4 mt-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Visits</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics?.total_visits ?? 0}</div>
                <p className="text-xs text-muted-foreground">Last {analytics?.period_days ?? 30} days</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Unique Visitors</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics?.unique_visitors ?? 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Chatbot Queries</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics?.total_chatbot_queries ?? 0}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Subscribers</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{analytics?.subscriber_count ?? 0}</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Features</CardTitle>
              <CardDescription>Toggle which sections appear on your public Trust Center.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                { key: "show_certifications", label: "Certifications", desc: "Display compliance certifications and badges", icon: Shield },
                { key: "show_controls", label: "Controls & Tests", desc: "Show real-time control monitoring status", icon: BarChart3 },
                { key: "show_policies", label: "Policies", desc: "Display active security policies", icon: FileText },
                { key: "show_ai_chatbot", label: "AI Chatbot", desc: "Let visitors ask questions about your security", icon: Bot },
                { key: "show_subscribe", label: "Email Subscriptions", desc: "Allow visitors to subscribe for updates", icon: Bell },
                { key: "show_document_requests", label: "Document Access", desc: "Allow visitors to request gated documents", icon: Download },
              ].map((feature) => (
                <div key={feature.key} className="flex items-center justify-between rounded-lg border p-4">
                  <div className="flex items-center gap-3">
                    <feature.icon className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{feature.label}</p>
                      <p className="text-sm text-muted-foreground">{feature.desc}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleToggle(feature.key, !(settings?.[feature.key] ?? false))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      settings?.[feature.key] ? "bg-primary" : "bg-muted"
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        settings?.[feature.key] ? "translate-x-6" : "translate-x-1"
                      }`}
                    />
                  </button>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="branding" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Page Branding</CardTitle>
              <CardDescription>Customize the look and feel of your Trust Center.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="page-title">Page Title</Label>
                <Input
                  id="page-title"
                  defaultValue={settings?.page_title ?? "Trust Center"}
                  onBlur={(e) => updateSettingsMutation.mutate({ page_title: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="hero-headline">Hero Headline</Label>
                <Input
                  id="hero-headline"
                  defaultValue={settings?.hero_headline ?? "Your Trust, Our Priority"}
                  onBlur={(e) => updateSettingsMutation.mutate({ hero_headline: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="hero-subtext">Hero Subtext</Label>
                <textarea
                  id="hero-subtext"
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  defaultValue={settings?.hero_subtext ?? ""}
                  onBlur={(e) => updateSettingsMutation.mutate({ hero_subtext: e.target.value })}
                  rows={3}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="brand-color">Brand Color</Label>
                <div className="flex gap-2">
                  <Input
                    id="brand-color"
                    type="color"
                    className="w-16 h-10 p-1"
                    defaultValue={settings?.brand_color ?? "#0f766e"}
                    onBlur={(e) => updateSettingsMutation.mutate({ brand_color: e.target.value })}
                  />
                  <Input
                    defaultValue={settings?.brand_color ?? "#0f766e"}
                    onBlur={(e) => updateSettingsMutation.mutate({ brand_color: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="logo-url">Logo URL</Label>
                <Input
                  id="logo-url"
                  placeholder="https://example.com/logo.png"
                  defaultValue={settings?.logo_url ?? ""}
                  onBlur={(e) => updateSettingsMutation.mutate({ logo_url: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="custom-domain">Custom Domain (optional)</Label>
                <Input
                  id="custom-domain"
                  placeholder="trust.yourcompany.com"
                  defaultValue={settings?.custom_domain ?? ""}
                  onBlur={(e) => updateSettingsMutation.mutate({ custom_domain: e.target.value })}
                />
              </div>
              <Button onClick={handleSaveSettings}>
                <Save className="mr-2 h-4 w-4" />Save Branding
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documents" className="space-y-4 mt-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Gated Documents</h3>
            <Dialog open={docDialogOpen} onOpenChange={setDocDialogOpen}>
              <DialogTrigger asChild>
                <Button><Plus className="mr-2 h-4 w-4" />Add Document</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Trust Center Document</DialogTitle>
                  <DialogDescription>Documents can be public or require NDA access.</DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label>Title</Label>
                    <Input value={docTitle} onChange={(e) => setDocTitle(e.target.value)} placeholder="SOC 2 Type II Report" />
                  </div>
                  <div>
                    <Label>Description</Label>
                    <textarea
                      className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                      value={docDescription}
                      onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setDocDescription(e.target.value)}
                      rows={3}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Requires NDA</Label>
                    <button
                      onClick={() => setDocNda(!docNda)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${docNda ? "bg-primary" : "bg-muted"}`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${docNda ? "translate-x-6" : "translate-x-1"}`} />
                    </button>
                  </div>
                  <div className="flex items-center justify-between">
                    <Label>Publicly Listed</Label>
                    <button
                      onClick={() => setDocPublic(!docPublic)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${docPublic ? "bg-primary" : "bg-muted"}`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${docPublic ? "translate-x-6" : "translate-x-1"}`} />
                    </button>
                  </div>
                </div>
                <DialogFooter>
                  <Button onClick={() => createDocMutation.mutate({
                    title: docTitle,
                    description: docDescription,
                    document_type: "report",
                    requires_nda: docNda,
                    is_public: docPublic,
                  })}>
                    Create Document
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {docsLoading ? (
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent mx-auto" />
          ) : (documents || []).length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No documents yet. Add SOC 2 reports, pentest results, or policy documents.
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {(documents || []).map((doc: any) => (
                <Card key={doc.id}>
                  <CardContent className="flex items-center justify-between py-4">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="font-medium">{doc.title}</p>
                        <div className="flex gap-2 mt-1">
                          <Badge variant="outline">{doc.document_type}</Badge>
                          {doc.requires_nda && <Badge variant="secondary">NDA Required</Badge>}
                          {doc.is_public && <Badge variant="default">Public</Badge>}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">{doc.download_count} downloads</span>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => deleteDocMutation.mutate(doc.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="requests" className="space-y-4 mt-4">
          <h3 className="text-lg font-semibold">Document Access Requests</h3>
          {(accessRequests || []).length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No pending access requests.
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {(accessRequests || []).map((req: any) => (
                <Card key={req.id}>
                  <CardContent className="flex items-center justify-between py-4">
                    <div>
                      <p className="font-medium">{req.requester_email}</p>
                      <p className="text-sm text-muted-foreground">
                        {req.requester_name} {req.requester_company ? `· ${req.requester_company}` : ""}
                      </p>
                      <div className="flex gap-2 mt-1">
                        <Badge variant={req.status === "pending" ? "secondary" : req.status === "approved" ? "default" : "destructive"}>
                          {req.status}
                        </Badge>
                        {req.nda_accepted && <Badge variant="outline">NDA Accepted</Badge>}
                      </div>
                    </div>
                    {req.status === "pending" && (
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={() => approveRequestMutation.mutate({ id: req.id, status: "approved" })}
                        >
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => approveRequestMutation.mutate({ id: req.id, status: "rejected" })}
                        >
                          Reject
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          <h3 className="text-lg font-semibold mt-6">Subscribers</h3>
          {(subscribers || []).length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No subscribers yet.
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {(subscribers || []).map((sub: any) => (
                <Card key={sub.id}>
                  <CardContent className="flex items-center justify-between py-4">
                    <div>
                      <p className="font-medium">{sub.email}</p>
                      <p className="text-sm text-muted-foreground">
                        {sub.name} {sub.company ? `· ${sub.company}` : ""}
                      </p>
                    </div>
                    <Badge variant={sub.subscribed ? "default" : "secondary"}>
                      {sub.subscribed ? "Active" : "Unsubscribed"}
                    </Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Visitor Analytics</CardTitle>
              <CardDescription>Track engagement with your Trust Center.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">Total Visits</p>
                  <p className="text-3xl font-bold">{analytics?.total_visits ?? 0}</p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">Unique Visitors</p>
                  <p className="text-3xl font-bold">{analytics?.unique_visitors ?? 0}</p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">Chatbot Queries</p>
                  <p className="text-3xl font-bold">{analytics?.total_chatbot_queries ?? 0}</p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">Document Downloads</p>
                  <p className="text-3xl font-bold">{analytics?.total_document_downloads ?? 0}</p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">Subscribers</p>
                  <p className="text-3xl font-bold">{analytics?.subscriber_count ?? 0}</p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">Pending Requests</p>
                  <p className="text-3xl font-bold">{analytics?.pending_access_requests ?? 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default TrustCenterPage;
