from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    root_path: str = Field(..., description="Absolute path to codebase on disk")
    framework: str = Field(default="auto", pattern="^(auto|django|fastapi|python)$")
    github_repo: str = Field(default="", description="owner/repo for PR comments")


class ProjectUpdate(BaseModel):
    watch_enabled: bool | None = None
    github_repo: str | None = None
    slack_webhook: str | None = None
    badge_public: bool | None = None


class ProjectOut(BaseModel):
    id: int
    name: str
    root_path: str
    framework: str
    watch_enabled: bool = False
    github_repo: str = ""
    plan: str = "starter"
    public_slug: str = ""
    badge_public: bool = True
    last_score: int = 0
    created_at: datetime


class BadgeEmbedOut(BaseModel):
    public_slug: str
    score: int | None = None
    badge_enabled: bool = True
    image_url: str
    project_url: str
    markdown: str
    hosted_image_url: str
    hosted_project_url: str


class PublicProjectOut(BaseModel):
    slug: str
    name: str
    score: int | None = None
    grade: str | None = None
    framework: str
    routes_found: int = 0
    last_scanned_at: str | None = None
    project_url: str


class HostedPreviewIn(BaseModel):
    github_url: str = Field(..., min_length=10, max_length=500)


class HostedPreviewOut(BaseModel):
    github_url: str
    repo: str
    framework: str
    routes_found: int
    files_scanned: int
    score: int
    grade: str
    summary: str
    breakdown: dict
    drift: dict
    hosted: bool = True
    message: str

    model_config = {"from_attributes": True}


class ArtifactOut(BaseModel):
    id: int
    kind: str
    title: str
    content: str
    file_path: str
    polished: bool = False

    model_config = {"from_attributes": True}


class ScanOut(BaseModel):
    id: int
    project_id: int
    status: str
    summary: str
    stats: str
    trigger: str = "manual"
    created_at: datetime
    artifacts: list[ArtifactOut] = []

    model_config = {"from_attributes": True}


class ContextOut(BaseModel):
    what_happened: str
    who: str
    why_it_matters: str
    what_next: str


class GitHubPrCommentIn(BaseModel):
    pr_number: int = Field(..., ge=1)
    github_repo: str | None = Field(
        default=None, description="owner/repo; uses project default if omitted"
    )


class PolishOut(BaseModel):
    artifact_id: int
    content: str
    polished: bool


class FeatureRow(BaseModel):
    name: str
    starter: bool
    pro: bool
    enterprise: bool


class PricingCatalog(BaseModel):
    currency: str
    starter_price_usd: int
    pro_price_usd: int
    pro_interval: str
    pro_trial_days: int
    annual_discount_percent: int
    starter_annual_usd: int
    pro_annual_usd: int
    feature_matrix: list[FeatureRow]
    stripe_live: bool


class BillingStatusOut(BaseModel):
    plan: str
    is_pro: bool
    is_starter: bool
    features: list[str]
    stripe_configured: bool
    catalog: PricingCatalog


class CheckoutOut(BaseModel):
    mode: str
    url: str | None = None
    session_id: str | None = None
    tier: str | None = None


class FeaturesOut(BaseModel):
    github: bool
    ai_polish: bool
    ai_suite: bool
    watch: bool
    stripe: bool


class BreakingChangeItem(BaseModel):
    path: str
    change: str
    classification: str
    reason: str


class BreakingChangeOut(BaseModel):
    summary: str
    items: list[BreakingChangeItem]
    breaking_count: int
    additive_count: int


class AiDescriptionsOut(BaseModel):
    filled: int
    gaps_found: int
    openapi: str
    updates: list[dict] = []


class AiMigrationNoteOut(BaseModel):
    note: str
    triage: BreakingChangeOut


class AiBreakingChangeOut(BreakingChangeOut):
    pass


class DocstringMismatch(BaseModel):
    method: str
    path: str
    handler: str
    docstring: str
    openapi_summary: str
    suggestion: str


class AiReconcileOut(BaseModel):
    mismatches: list[DocstringMismatch]
    count: int


class AiTestsOut(BaseModel):
    content: str
    enhanced: int


class AiChatIn(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


class AiChatOut(BaseModel):
    answer: str
    sources: list[dict] = []


class ScoreBreakdown(BaseModel):
    documentation_pct: float
    test_coverage_pct: float
    fully_covered_pct: float
    freshness_pct: float
    model_documentation_pct: float = 0.0


class ScoreGaps(BaseModel):
    no_test: int
    no_docs: int
    red_routes: int
    amber_routes: int


class ScoreOut(BaseModel):
    score: int
    grade: str
    breakdown: ScoreBreakdown
    gaps: ScoreGaps
    summary: str


class RouteCoverage(BaseModel):
    method: str
    path: str
    handler: str
    summary: str = ""
    has_test: bool
    has_docs: bool
    status: str
    status_label: str = ""


class DriftOut(BaseModel):
    drift_detected: bool
    commits_behind: int
    message: str
    spec_path: str | None = None


class PrDiffOut(BaseModel):
    added_paths: list[str] = []
    removed_paths: list[str] = []
    routes_changed: int = 0
    summary: str = ""


class AiSuiteOut(BaseModel):
    ai_available: bool
    plan: str
    description_gaps: int
    docstring_mismatches: int
    breaking_change: BreakingChangeOut
    pr_diff: PrDiffOut | None = None
    score: int | None = None


class MetricPair(BaseModel):
    current: int
    total: int


class HealthMetrics(BaseModel):
    routes_documented: MetricPair
    routes_documented_delta: int = 0
    tests_generated: dict
    models_documented: dict
    spec_drift: int = 0
    spec_in_sync: bool = True


class HealthAlerts(BaseModel):
    test_gap: dict | None = None
    pr_update: dict | None = None
    description_gap: dict | None = None


class ScanAiInsights(BaseModel):
    description_gaps: int = 0
    descriptions_filled: int = 0
    migration_note: str | None = None
    auto_ran: bool = False


class HealthOut(BaseModel):
    score: ScoreOut
    coverage: list[RouteCoverage]
    drift: DriftOut
    pr_diff: PrDiffOut | None = None
    route_count: int = 0
    models_count: int = 0
    metrics: HealthMetrics | None = None
    alerts: HealthAlerts | None = None
    ai: ScanAiInsights | None = None
    synced_files: list[str] = []
    last_scanned_at: str | None = None


class CiTemplateOut(BaseModel):
    filename: str
    content: str


class FrameworkRoadmapItem(BaseModel):
    name: str
    status: str
    detail: str


class RoadmapOut(BaseModel):
    tagline: str
    frameworks: list[FrameworkRoadmapItem]


class SlackAlertIn(BaseModel):
    webhook_url: str


class NotionPushIn(BaseModel):
    notion_token: str | None = None
    parent_page_id: str | None = None
    title: str | None = None


class TeamDashboardSummary(BaseModel):
    total_projects: int
    scored_projects: int
    avg_score: int | None = None
    avg_documentation_pct: float | None = None
    avg_test_coverage_pct: float | None = None
    drifted_this_week: int
    needs_attention: int


class ProjectDashboardRow(BaseModel):
    id: int
    name: str
    root_path: str
    framework: str
    github_repo: str | None = None
    watch_enabled: bool = False
    score: int | None = None
    grade: str | None = None
    last_scanned_at: str | None = None
    documentation_pct: float | None = None
    test_coverage_pct: float | None = None
    routes_found: int = 0
    drift_detected: bool = False
    spec_in_sync: bool = True
    commits_behind: int = 0
    score_delta_7d: int | None = None
    needs_attention: bool = False
    never_scanned: bool = False
    drift_this_week: bool = False


class DriftedProjectRow(ProjectDashboardRow):
    reason: str


class TrendWeek(BaseModel):
    week: str
    label: str
    avg_score: int
    scan_count: int


class ScorePoint(BaseModel):
    at: str | None
    score: int


class ProjectTrend(BaseModel):
    project_id: int
    project_name: str
    points: list[ScorePoint]


class TeamDashboardOut(BaseModel):
    summary: TeamDashboardSummary
    projects: list[ProjectDashboardRow]
    drifted_this_week: list[DriftedProjectRow]
    team_trend: list[TrendWeek]
    project_trends: list[ProjectTrend]
