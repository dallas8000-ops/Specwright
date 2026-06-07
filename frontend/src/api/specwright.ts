import axios from "axios";

const configuredApiUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, "");

const apiBase = configuredApiUrl
  ? configuredApiUrl.endsWith("/api/v1")
    ? configuredApiUrl
    : `${configuredApiUrl}/api/v1`
  : "https://specwright-api-production.up.railway.app/api/v1";

export const specwright = axios.create({
  baseURL: apiBase,
  headers: { "Content-Type": "application/json" },
});

export interface Project {
  id: number;
  name: string;
  root_path: string;
  framework: string;
  watch_enabled: boolean;
  github_repo: string;
  plan: string;
  created_at: string;
}

export interface Features {
  github: boolean;
  ai_polish: boolean;
  ai_suite: boolean;
  watch: boolean;
  stripe: boolean;
}

export interface FeatureRow {
  name: string;
  starter: boolean;
  pro: boolean;
  enterprise: boolean;
}

export interface PricingCatalog {
  currency: string;
  starter_price_usd: number;
  pro_price_usd: number;
  pro_interval: string;
  pro_trial_days: number;
  annual_discount_percent: number;
  starter_annual_usd: number;
  pro_annual_usd: number;
  feature_matrix: FeatureRow[];
  stripe_live: boolean;
}

export interface BillingStatus {
  plan: string;
  is_pro: boolean;
  is_starter: boolean;
  features: string[];
  stripe_configured: boolean;
  catalog: PricingCatalog;
}

export interface Artifact {
  id: number;
  kind: string;
  title: string;
  content: string;
  file_path: string;
  polished?: boolean;
}

export async function updateProject(
  projectId: number,
  body: { watch_enabled?: boolean; github_repo?: string }
) {
  return specwright.patch<Project>(`/projects/${projectId}`, body);
}

export async function postPrComment(
  projectId: number,
  body: { pr_number: number; github_repo?: string }
) {
  return (
    await specwright.post<{ posted: boolean; html_url?: string }>(
      `/projects/${projectId}/github/pr-comment`,
      body
    )
  ).data;
}

export async function polishArtifact(projectId: number, artifactId: number) {
  return specwright.post<{ content: string }>(
    `/projects/${projectId}/artifacts/${artifactId}/polish`
  );
}

export async function startCheckout(tier: "starter" | "pro", annual?: boolean) {
  const params = new URLSearchParams({ tier });
  if (annual) params.set("annual", "true");
  return specwright.post<{ url?: string; mode: string; tier?: string }>(
    `/billing/checkout?${params.toString()}`
  );
}

export async function activateMockPro(projectId: number) {
  return specwright.post(`/billing/activate-mock/${projectId}`);
}

export interface Scan {
  id: number;
  project_id: number;
  status: string;
  summary: string;
  stats: string;
  created_at: string;
  artifacts: Artifact[];
}

export interface Context {
  what_happened: string;
  who: string;
  why_it_matters: string;
  what_next: string;
}

export interface HealthMetrics {
  routes_documented: { current: number; total: number };
  routes_documented_delta: number;
  tests_generated: { current: number; total: number; uncovered: number };
  models_documented: { current: number; total: number; missing: number };
  spec_drift: number;
  spec_in_sync: boolean;
}

export interface HealthAlerts {
  test_gap?: {
    count: number;
    samples: string[];
    message: string;
  } | null;
  pr_update?: {
    routes_changed: number;
    added_count: number;
    summary: string;
    message: string;
    migration_note?: string | null;
  } | null;
  description_gap?: {
    count: number;
    filled?: number;
    message: string;
  } | null;
}

export interface ScanAiInsights {
  description_gaps: number;
  descriptions_filled: number;
  migration_note?: string | null;
  auto_ran: boolean;
}

export async function fillDescriptions(projectId: number) {
  return specwright.post<{ filled: number; gaps_found: number; openapi: string }>(
    `/projects/${projectId}/ai/descriptions`
  );
}

export interface ProjectHealth {
  score: {
    score: number;
    grade: string;
    summary: string;
    breakdown: {
      documentation_pct: number;
      test_coverage_pct: number;
      fully_covered_pct: number;
      freshness_pct: number;
      model_documentation_pct?: number;
    };
    gaps: { no_test: number; no_docs: number; red_routes: number; amber_routes: number };
  };
  coverage: Array<{
    method: string;
    path: string;
    handler: string;
    summary?: string;
    has_test: boolean;
    has_docs: boolean;
    status: string;
    status_label?: string;
  }>;
  drift: { drift_detected: boolean; commits_behind: number; message: string };
  pr_diff?: { added_paths: string[]; removed_paths: string[]; routes_changed: number; summary: string } | null;
  synced_files: string[];
  route_count: number;
  models_count?: number;
  metrics?: HealthMetrics | null;
  alerts?: HealthAlerts | null;
  ai?: ScanAiInsights | null;
  last_scanned_at?: string | null;
}

export async function fetchCiTemplate(projectId: number) {
  return specwright.get<{ filename: string; content: string }>(
    `/projects/${projectId}/ci-template`
  );
}

export async function pushNotion(projectId: number, body?: { title?: string }) {
  return specwright.post<{ page_url?: string }>(`/projects/${projectId}/export/notion`, body ?? {});
}

export async function setSlackWebhook(projectId: number, webhook_url: string) {
  return specwright.post(`/projects/${projectId}/alerts/slack`, { webhook_url });
}

export interface TeamDashboardSummary {
  total_projects: number;
  scored_projects: number;
  avg_score: number | null;
  avg_documentation_pct: number | null;
  avg_test_coverage_pct: number | null;
  drifted_this_week: number;
  needs_attention: number;
}

export interface ProjectDashboardRow {
  id: number;
  name: string;
  root_path: string;
  framework: string;
  github_repo?: string | null;
  watch_enabled: boolean;
  score: number | null;
  grade?: string | null;
  last_scanned_at?: string | null;
  documentation_pct?: number | null;
  test_coverage_pct?: number | null;
  routes_found: number;
  drift_detected: boolean;
  spec_in_sync: boolean;
  commits_behind: number;
  score_delta_7d?: number | null;
  needs_attention: boolean;
  never_scanned: boolean;
  drift_this_week: boolean;
}

export interface TeamDashboard {
  summary: TeamDashboardSummary;
  projects: ProjectDashboardRow[];
  drifted_this_week: (ProjectDashboardRow & { reason: string })[];
  team_trend: { week: string; label: string; avg_score: number; scan_count: number }[];
  project_trends: {
    project_id: number;
    project_name: string;
    points: { at: string | null; score: number }[];
  }[];
}

export async function fetchTeamDashboard(): Promise<TeamDashboard> {
  return (await specwright.get<TeamDashboard>("/dashboard")).data;
}

export interface BadgeEmbed {
  public_slug: string;
  score: number | null;
  badge_enabled: boolean;
  image_url: string;
  project_url: string;
  markdown: string;
  hosted_image_url: string;
  hosted_project_url: string;
}

export async function fetchBadgeEmbed(projectId: number): Promise<BadgeEmbed> {
  return (await specwright.get<BadgeEmbed>(`/projects/${projectId}/badge-embed`)).data;
}
