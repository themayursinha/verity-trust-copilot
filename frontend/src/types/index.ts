export interface Organization {
  id: string;
  name: string;
  slug: string;
  max_seats: number;
  license_key: string | null;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: "admin" | "editor" | "viewer" | "member";
  is_active: boolean;
  org_id: string;
  created_at: string;
  updated_at: string;
}

export interface EvidenceRecord {
  id: string;
  org_id: string;
  title: string;
  type: string;
  frameworks: string[];
  control_ids: string[];
  last_reviewed: string;
  owner: string;
  summary: string;
  snippets: string[];
  created_at: string;
  updated_at: string;
}

export interface Citation {
  source_id: string;
  title: string;
  citation: string;
  last_reviewed: string;
}

export interface FreshnessItem {
  source: string;
  status: "fresh" | "stale" | "outdated";
  last_reviewed: string;
  age_days: number;
}

export interface AnswerGeneration {
  id: string;
  org_id: string;
  as_of_date: string | null;
  confidence_counts: { high: number; medium: number; low: number };
  answers: Answer[];
  created_at: string;
}

export interface Answer {
  id: string;
  generation_id: string;
  question: string;
  answer_text: string;
  confidence: "high" | "medium" | "low" | null;
  confidence_rationale: string | null;
  needs_human_review: boolean;
  citations: Citation[];
  freshness: FreshnessItem[];
  created_at: string;
}

export interface Approval {
  id: string;
  answer_id: string;
  user_id: string;
  status: "approved" | "rejected" | "unreviewed";
  notes: string | null;
  created_at: string;
}

export interface Policy {
  id: string;
  org_id: string;
  title: string;
  category: string;
  content: string;
  status: "draft" | "active" | "archived";
  version: number;
  review_interval_months: number;
  next_review: string | null;
  created_at: string;
  updated_at: string;
}

export interface Pentest {
  id: string;
  org_id: string;
  title: string;
  scope: string;
  methodology: string;
  start_date: string | null;
  end_date: string | null;
  status: "planned" | "in-progress" | "completed";
  findings: Finding[];
  created_at: string;
  updated_at: string;
}

export interface Finding {
  id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  description: string;
  remediation: string;
  status: "open" | "in-progress" | "resolved" | "accepted";
  assigned_to: string;
  due_date: string | null;
}

export interface ActivityLog {
  action: string;
  detail: string;
  timestamp: string;
}

export interface FrameworkCoverage {
  id: string;
  coverage: number;
  evidence_count: number;
  control_count: number;
}

export interface DashboardData {
  frameworks: FrameworkCoverage[];
  evidence: {
    total: number;
    fresh: number;
    stale: number;
    frameworks_covered: number;
  };
  policies: {
    total: number;
    active: number;
    draft: number;
    upcoming_reviews: number;
  };
  approvals: {
    total: number;
    approved: number;
    rejected: number;
    unreviewed: number;
  };
  recent_activity: ActivityLog[];
}

export interface EvidenceStats {
  total: number;
  fresh: number;
  stale: number;
  outdated: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  organization_name: string;
  display_name: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
  organization: Organization;
}
