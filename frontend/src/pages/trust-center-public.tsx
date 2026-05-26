import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import {
  Shield,
  FileText,
  Bell,
  Send,
  Check,
  Download,
  Loader2,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

interface TrustCenterData {
  organization: { name: string; slug: string };
  settings: {
    enabled: boolean;
    page_title: string;
    hero_headline: string;
    hero_subtext: string;
    brand_color: string;
    logo_url: string;
    show_certifications: boolean;
    show_controls: boolean;
    show_policies: boolean;
    show_ai_chatbot: boolean;
    show_subscribe: boolean;
    show_document_requests: boolean;
    require_nda: boolean;
  };
  certifications: Array<{ id: string; title: string; frameworks: string[]; last_reviewed: string | null }>;
  policies: Array<{ id: string; name: string; status: string; last_reviewed: string | null; version: string | null }>;
  documents: Array<{ id: string; title: string; description: string; document_type: string; requires_nda: boolean; download_count: number }>;
}

export default function PublicTrustCenter() {
  const { orgSlug } = useParams<{ orgSlug: string }>();
  const [data, setData] = useState<TrustCenterData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<Array<{ role: string; content: string }>>([
    { role: "assistant", content: "Hi! I can answer questions about our security and compliance program. What would you like to know?" },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [subscribeEmail, setSubscribeEmail] = useState("");
  const [subscribeName, setSubscribeName] = useState("");
  const [subscribeCompany, setSubscribeCompany] = useState("");
  const [subscribed, setSubscribed] = useState(false);
  const [accessEmail, setAccessEmail] = useState("");
  const [accessName, setAccessName] = useState("");
  const [accessCompany, setAccessCompany] = useState("");
  const [accessRequested, setAccessRequested] = useState(false);
  const [showAccessForm, setShowAccessForm] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const resp = await axios.get(`/api/v1/public/trust-center/${orgSlug}`);
        setData(resp.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || "Trust Center not found");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [orgSlug]);

  const handleChat = async () => {
    if (!chatInput.trim()) return;
    const question = chatInput;
    setChatMessages((prev) => [...prev, { role: "user", content: question }]);
    setChatInput("");
    setChatLoading(true);
    try {
      const resp = await axios.post(`/api/v1/public/trust-center/${orgSlug}/chat`, { question });
      setChatMessages((prev) => [...prev, { role: "assistant", content: resp.data.answer }]);
    } catch {
      setChatMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I couldn't process that question. Please try again." }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleSubscribe = async () => {
    if (!subscribeEmail) return;
    try {
      await axios.post(`/api/v1/public/trust-center/${orgSlug}/subscribe`, {
        email: subscribeEmail,
        name: subscribeName,
        company: subscribeCompany,
      });
      setSubscribed(true);
    } catch {}
  };

  const handleAccessRequest = async () => {
    if (!accessEmail) return;
    try {
      await axios.post(`/api/v1/public/trust-center/${orgSlug}/request-access`, {
        email: accessEmail,
        name: accessName,
        company: accessCompany,
        nda_accepted: true,
      });
      setAccessRequested(true);
    } catch {}
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="py-8 text-center">
            <Shield className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium">Trust Center Not Available</p>
            <p className="text-sm text-muted-foreground mt-2">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const brandColor = data.settings.brand_color || "#0f766e";

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b" style={{ borderColor: brandColor }}>
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              {data.settings.logo_url && (
                <img src={data.settings.logo_url} alt="Logo" className="h-8 mb-2" />
              )}
              <h1 className="text-3xl font-bold">{data.settings.page_title || "Trust Center"}</h1>
              <p className="text-muted-foreground mt-1">{data.organization.name}</p>
            </div>
            {data.settings.show_ai_chatbot && (
              <Button onClick={() => setChatOpen(!chatOpen)} style={{ backgroundColor: brandColor }}>
                <Shield className="mr-2 h-4 w-4" />
                Ask AI
              </Button>
            )}
          </div>
        </div>
      </header>

      <section className="py-16" style={{ backgroundColor: brandColor + "0a" }}>
        <div className="max-w-6xl mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-4">{data.settings.hero_headline || "Your Trust, Our Priority"}</h2>
          {data.settings.hero_subtext && (
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">{data.settings.hero_subtext}</p>
          )}
        </div>
      </section>

      <main className="max-w-6xl mx-auto px-4 py-12 space-y-12">
        {data.settings.show_certifications && (data.certifications || []).length > 0 && (
          <section>
            <h3 className="text-2xl font-bold mb-6">Certifications</h3>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {(data.certifications || []).map((cert) => (
                <Card key={cert.id}>
                  <CardContent className="py-6">
                    <div className="flex items-start gap-3">
                      <Shield className="h-8 w-8" style={{ color: brandColor }} />
                      <div>
                        <p className="font-semibold">{cert.title}</p>
                        <div className="flex flex-wrap gap-1 mt-2">
                          {(cert.frameworks || []).map((fw) => (
                            <Badge key={fw} variant="outline" className="text-xs">{fw.toUpperCase()}</Badge>
                          ))}
                        </div>
                        {cert.last_reviewed && (
                          <p className="text-xs text-muted-foreground mt-2">
                            Reviewed: {cert.last_reviewed}
                          </p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        )}

        {data.settings.show_policies && (data.policies || []).length > 0 && (
          <section>
            <h3 className="text-2xl font-bold mb-6">Active Policies</h3>
            <div className="grid gap-4 md:grid-cols-2">
              {(data.policies || []).map((policy) => (
                <Card key={policy.id}>
                  <CardContent className="flex items-center justify-between py-4">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5" style={{ color: brandColor }} />
                      <div>
                        <p className="font-medium">{policy.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {policy.status} {policy.version ? `· v${policy.version}` : ""}
                        </p>
                      </div>
                    </div>
                    <Badge variant={policy.status === "active" ? "default" : "secondary"}>{policy.status}</Badge>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        )}

        {data.settings.show_document_requests && (data.documents || []).length > 0 && (
          <section>
            <h3 className="text-2xl font-bold mb-6">Documents</h3>
            <div className="space-y-3">
              {(data.documents || []).map((doc) => (
                <Card key={doc.id}>
                  <CardContent className="flex items-center justify-between py-4">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5" style={{ color: brandColor }} />
                      <div>
                        <p className="font-medium">{doc.title}</p>
                        <p className="text-sm text-muted-foreground">{doc.description}</p>
                      </div>
                    </div>
                    {doc.requires_nda ? (
                      <Button variant="outline" size="sm" onClick={() => setShowAccessForm(true)}>
                        <Download className="mr-2 h-4 w-4" />Request Access
                      </Button>
                    ) : (
                      <Button variant="outline" size="sm">
                        <Download className="mr-2 h-4 w-4" />Download
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        )}

        {data.settings.show_subscribe && (
          <section>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5" style={{ color: brandColor }} />
                  Stay Updated
                </CardTitle>
                <CardDescription>Get notified about security updates, new certifications, and policy changes.</CardDescription>
              </CardHeader>
              <CardContent>
                {subscribed ? (
                  <div className="flex items-center gap-2 text-green-600">
                    <Check className="h-5 w-5" />
                    <span>Subscribed! You'll receive security updates.</span>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <Input
                        placeholder="Your email"
                        value={subscribeEmail}
                        onChange={(e) => setSubscribeEmail(e.target.value)}
                        className="flex-1"
                      />
                      <Input
                        placeholder="Name (optional)"
                        value={subscribeName}
                        onChange={(e) => setSubscribeName(e.target.value)}
                      />
                      <Input
                        placeholder="Company (optional)"
                        value={subscribeCompany}
                        onChange={(e) => setSubscribeCompany(e.target.value)}
                      />
                    </div>
                    <Button onClick={handleSubscribe} style={{ backgroundColor: brandColor }}>
                      <Bell className="mr-2 h-4 w-4" />Subscribe
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </section>
        )}
      </main>

      {showAccessForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="max-w-md w-full mx-4">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Request Document Access</CardTitle>
                <Button variant="ghost" size="icon" onClick={() => setShowAccessForm(false)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <CardDescription>This document requires an NDA before access is granted.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {accessRequested ? (
                <div className="flex items-center gap-2 text-green-600 py-4">
                  <Check className="h-5 w-5" />
                  <span>Access requested! You'll be notified when approved.</span>
                </div>
              ) : (
                <>
                  <Input
                    placeholder="Work email"
                    value={accessEmail}
                    onChange={(e) => setAccessEmail(e.target.value)}
                  />
                  <Input
                    placeholder="Full name"
                    value={accessName}
                    onChange={(e) => setAccessName(e.target.value)}
                  />
                  <Input
                    placeholder="Company"
                    value={accessCompany}
                    onChange={(e) => setAccessCompany(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    By requesting access, you agree to the terms of our Non-Disclosure Agreement.
                  </p>
                  <Button onClick={handleAccessRequest} className="w-full" style={{ backgroundColor: brandColor }}>
                    Request Access
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {chatOpen && (
        <div className="fixed bottom-6 right-6 z-50">
          <Card className="w-96 shadow-xl">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Shield className="h-4 w-4" style={{ color: brandColor }} />
                  Security AI Assistant
                </CardTitle>
                <Button variant="ghost" size="icon" onClick={() => setChatOpen(false)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="h-80 overflow-y-auto p-4 space-y-3">
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                        msg.role === "user"
                          ? "text-white"
                          : "bg-muted"
                      }`}
                      style={msg.role === "user" ? { backgroundColor: brandColor } : {}}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex justify-start">
                    <div className="bg-muted rounded-lg px-3 py-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                  </div>
                )}
              </div>
              <div className="border-t p-3 flex gap-2">
                <Input
                  placeholder="Ask about our security..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleChat()}
                />
                <Button size="icon" onClick={handleChat} disabled={chatLoading} style={{ backgroundColor: brandColor }}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <footer className="border-t py-8 mt-16">
        <div className="max-w-6xl mx-auto px-4 text-center text-sm text-muted-foreground">
          Powered by Verity Trust Copilot
        </div>
      </footer>
    </div>
  );
}
