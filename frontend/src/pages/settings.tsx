import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Copy, Check, Moon, Sun, UserPlus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/hooks/useAuth";
import { getOrgMembers, inviteMember, updateMember, removeMember, getOrgInfo, getLicenseStatus, activateLicense } from "@/lib/api";

function SettingsPage() {
  const { user, organization } = useAuth();
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState(false);
  const [isDark, setIsDark] = useState(
    () => document.documentElement.classList.contains("dark")
  );
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("member");
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [licenseKeyInput, setLicenseKeyInput] = useState("");

  const { data: orgInfo } = useQuery({
    queryKey: ["orgInfo"],
    queryFn: getOrgInfo,
  });

  const { data: members, isLoading: membersLoading } = useQuery({
    queryKey: ["members"],
    queryFn: getOrgMembers,
  });

  const { data: licenseStatus } = useQuery({
    queryKey: ["licenseStatus"],
    queryFn: getLicenseStatus,
  });

  const activateMutation = useMutation({
    mutationFn: (key: string) => activateLicense(key),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["licenseStatus"] });
      queryClient.invalidateQueries({ queryKey: ["orgInfo"] });
      setLicenseKeyInput("");
    },
  });

  const inviteMutation = useMutation({
    mutationFn: ({ email, role }: { email: string; role: string }) => inviteMember(email, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members"] });
      queryClient.invalidateQueries({ queryKey: ["orgInfo"] });
      setInviteDialogOpen(false);
      setInviteEmail("");
      setInviteRole("member");
    },
  });

  const updateMemberMutation = useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: { role?: string; is_active?: boolean } }) =>
      updateMember(userId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members"] });
    },
  });

  const removeMemberMutation = useMutation({
    mutationFn: (userId: string) => removeMember(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members"] });
      queryClient.invalidateQueries({ queryKey: ["orgInfo"] });
      setDeleteConfirmId(null);
    },
  });

  const toggleDarkMode = () => {
    const newDark = !isDark;
    setIsDark(newDark);
    document.documentElement.classList.toggle("dark", newDark);
    localStorage.setItem("theme", newDark ? "dark" : "light");
  };

  const copyLicenseKey = () => {
    if (orgInfo?.license_key) {
      navigator.clipboard.writeText(orgInfo.license_key);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleInvite = () => {
    if (!inviteEmail) return;
    inviteMutation.mutate({ email: inviteEmail, role: inviteRole });
  };

  const handleRoleChange = (userId: string, role: string) => {
    updateMemberMutation.mutate({ userId, data: { role } });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
        <p className="text-sm text-muted-foreground">
          Manage your organization and preferences
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Organization Profile</CardTitle>
          <CardDescription>Your organization&apos;s profile and license information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Organization Name</Label>
              <Input value={organization?.name ?? ""} readOnly />
            </div>
            <div className="space-y-2">
              <Label>Slug</Label>
              <Input value={organization?.slug ?? ""} readOnly />
            </div>
          </div>
          {orgInfo && (
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>
                <strong className="text-foreground">{orgInfo.seats_used}</strong> / {orgInfo.max_seats} seats used
              </span>
            </div>
          )}
          <Separator />
          <div className="space-y-2">
            <Label>License Key</Label>
            <div className="flex items-center gap-2">
              <Input
                value={orgInfo?.license_key ?? "No license key"}
                readOnly
                className="font-mono text-xs"
              />
              {orgInfo?.license_key && (
                <Button variant="outline" size="icon" onClick={copyLicenseKey}>
                  {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">License</CardTitle>
          <CardDescription>Manage your license key and view seat usage</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <Badge variant={licenseStatus?.status === "valid" ? "default" : licenseStatus?.status === "free" ? "secondary" : "destructive"}>
              {licenseStatus?.status === "valid" ? "Pro" : licenseStatus?.status === "free" ? "Free" : "Invalid"}
            </Badge>
            {licenseStatus?.max_seats != null && (
              <span className="text-sm text-muted-foreground">
                <strong className="text-foreground">{orgInfo?.seats_used ?? 0}</strong> / {licenseStatus.max_seats} seats
              </span>
            )}
          </div>
          {licenseStatus?.reason && (
            <p className="text-sm text-muted-foreground">{licenseStatus.reason}</p>
          )}
          {licenseStatus?.expires_at && (
            <p className="text-sm text-muted-foreground">
              Expires: {new Date(licenseStatus.expires_at * 1000).toLocaleDateString()}
            </p>
          )}
          <Separator />
          <div className="flex gap-2">
            <Input
              placeholder="Paste your license key..."
              value={licenseKeyInput}
              onChange={(e) => setLicenseKeyInput(e.target.value)}
              className="font-mono text-xs"
            />
            <Button
              onClick={() => licenseKeyInput && activateMutation.mutate(licenseKeyInput)}
              disabled={!licenseKeyInput || activateMutation.isPending}
            >
              {activateMutation.isPending ? "Activating..." : "Activate"}
            </Button>
          </div>
          {activateMutation.isError && (
            <p className="text-sm text-destructive">
              {(activateMutation.error as Error)?.message || "Failed to activate license"}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-lg">Members</CardTitle>
            <CardDescription>Team members with access to this organization</CardDescription>
          </div>
          <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <UserPlus className="mr-2 h-4 w-4" />
                Invite
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Invite Member</DialogTitle>
                <DialogDescription>Add a new member to your organization</DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="invite-email">Email address</Label>
                  <Input
                    id="invite-email"
                    type="email"
                    placeholder="colleague@company.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="invite-role">Role</Label>
                  <Select value={inviteRole} onValueChange={setInviteRole}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="member">Member</SelectItem>
                      <SelectItem value="editor">Editor</SelectItem>
                      <SelectItem value="viewer">Viewer</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setInviteDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleInvite} disabled={!inviteEmail || inviteMutation.isPending}>
                  {inviteMutation.isPending ? "Inviting..." : "Invite"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </CardHeader>
        <CardContent>
          {membersLoading ? (
            <p className="py-4 text-center text-sm text-muted-foreground">Loading members...</p>
          ) : !members || members.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">No members</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[120px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {members.map((m) => (
                  <TableRow key={m.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        {m.display_name}
                        {m.id === user?.id && (
                          <Badge variant="secondary" className="text-xs">You</Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>{m.email}</TableCell>
                    <TableCell>
                      <Select
                        value={m.role}
                        onValueChange={(role) => handleRoleChange(m.id, role)}
                        disabled={m.id === user?.id}
                      >
                        <SelectTrigger className="h-8 w-28">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="member">Member</SelectItem>
                          <SelectItem value="editor">Editor</SelectItem>
                          <SelectItem value="viewer">Viewer</SelectItem>
                          <SelectItem value="admin">Admin</SelectItem>
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Badge variant={m.is_active ? "default" : "secondary"}>
                        {m.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {m.id !== user?.id && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteConfirmId(m.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Appearance</CardTitle>
          <CardDescription>Customize your viewing experience</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Dark Mode</Label>
              <p className="text-sm text-muted-foreground">Toggle dark theme on or off</p>
            </div>
            <Button variant="outline" size="icon" onClick={toggleDarkMode}>
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={!!deleteConfirmId} onOpenChange={() => setDeleteConfirmId(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove Member</DialogTitle>
            <DialogDescription>
              Are you sure you want to remove this member? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmId(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => {
                if (deleteConfirmId) removeMemberMutation.mutate(deleteConfirmId);
              }}
              disabled={removeMemberMutation.isPending}
            >
              {removeMemberMutation.isPending ? "Removing..." : "Remove"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export { SettingsPage };
