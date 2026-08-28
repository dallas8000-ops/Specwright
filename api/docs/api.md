# API Reference
_Auto-generated from FastAPI routers._

| Method | Path | Handler | Summary |
|--------|------|---------|----------|
| **GET** | `/` | `root` | Root |
| **GET** | `/api/v1/badge/{slug}.svg` | `public_badge_svg` | Public Badge Svg |
| **POST** | `/api/v1/billing/checkout` | `create_checkout` | Create Checkout |
| **GET** | `/api/v1/billing/status` | `billing_status` | Billing Status |
| **POST** | `/api/v1/billing/webhook` | `stripe_webhook` | Stripe Webhook |
| **GET** | `/api/v1/dashboard` | `team_dashboard` | Multi-project scores, weekly drift, and team coverage trends. |
| **GET** | `/api/v1/features` | `feature_flags` | Feature Flags |
| **POST** | `/api/v1/github/webhook` | `github_webhook` | Github Webhook |
| **GET** | `/api/v1/health` | `health` | Health |
| **GET** | `/api/v1/health/billing` | `health_billing` | Health Billing |
| **POST** | `/api/v1/hosted/preview` | `hosted_github_preview` | Clone a public GitHub repo (shallow), run AST scan, return Specwright Score. |
| **GET** | `/api/v1/p/{slug}` | `public_landing_redirect` | Lightweight landing when someone clicks a README badge. |
| **GET** | `/api/v1/product` | `product` | Product |
| **GET** | `/api/v1/projects` | `list_projects` | List Projects |
| **POST** | `/api/v1/projects` | `create_project` | Create Project |
| **GET** | `/api/v1/projects/artifacts/{artifact_id}` | `get_artifact` | Get Artifact |
| **GET** | `/api/v1/projects/{project_id}` | `get_project` | Get Project |
| **PATCH** | `/api/v1/projects/{project_id}` | `update_project` | Update Project |
| **GET** | `/api/v1/projects/{project_id}/ai/breaking-changes` | `ai_breaking_changes` | Ai Breaking Changes |
| **POST** | `/api/v1/projects/{project_id}/ai/chat` | `ai_chat` | Ai Chat |
| **POST** | `/api/v1/projects/{project_id}/ai/descriptions` | `ai_fill_descriptions` | Ai Fill Descriptions |
| **POST** | `/api/v1/projects/{project_id}/ai/migration-note` | `ai_migration_note` | Ai Migration Note |
| **GET** | `/api/v1/projects/{project_id}/ai/reconcile` | `ai_reconcile` | Ai Reconcile |
| **GET** | `/api/v1/projects/{project_id}/ai/suite` | `ai_suite` | Non-LLM insights + counts; LLM actions available when configured. |
| **POST** | `/api/v1/projects/{project_id}/ai/tests` | `ai_enhance_tests` | Ai Enhance Tests |
| **POST** | `/api/v1/projects/{project_id}/alerts/slack` | `configure_slack` | Configure Slack |
| **POST** | `/api/v1/projects/{project_id}/alerts/test` | `test_slack_alert` | Test Slack Alert |
| **POST** | `/api/v1/projects/{project_id}/artifacts/{artifact_id}/polish` | `polish_artifact` | Polish Artifact |
| **GET** | `/api/v1/projects/{project_id}/badge-embed` | `project_badge_embed` | Project Badge Embed |
| **GET** | `/api/v1/projects/{project_id}/ci-template` | `ci_template` | Ci Template |
| **GET** | `/api/v1/projects/{project_id}/context` | `project_context` | Project Context |
| **POST** | `/api/v1/projects/{project_id}/export/notion` | `push_notion` | Push Notion |
| **POST** | `/api/v1/projects/{project_id}/github/pr-comment` | `github_pr_comment` | Github Pr Comment |
| **GET** | `/api/v1/projects/{project_id}/health` | `project_health` | Project Health |
| **POST** | `/api/v1/projects/{project_id}/scan` | `scan_project` | Scan Project |
| **GET** | `/api/v1/projects/{project_id}/scans` | `list_scans` | List Scans |
| **GET** | `/api/v1/projects/{project_id}/watch/events` | `watch_events` | Watch Events |
| **GET** | `/api/v1/public/projects/{slug}` | `public_project_card` | Public Project Card |
| **GET** | `/api/v1/roadmap` | `product_roadmap` | Product Roadmap |
| **GET** | `/badge/{slug}.svg` | `short_badge` | Shorter README URL (maps to hosted specwright.app/badge/{slug}). |
