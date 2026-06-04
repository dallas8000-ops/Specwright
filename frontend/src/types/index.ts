import type { MeaningContext } from "./meaning";

export type DepartmentType = "hr" | "legal" | "logistics" | "finance" | "it" | "operations" | "custom";

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  persona?: string;
}

export interface Case {
  id: number;
  title: string;
  case_type: string;
  case_type_label: string;
  stage: string;
  stage_label: string;
  subject_label: string;
  priority: string;
  department_name: string;
}

export interface ProactiveAlert {
  id: number;
  title: string;
  message: string;
  severity: string;
  acknowledged: boolean;
  meaning?: MeaningContext;
}

export interface Workflow {
  id: number;
  name: string;
  slug: string;
  description: string;
  status: "draft" | "active" | "paused" | "archived";
  trigger_type: string;
  department_name?: string;
  version: number;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  updated_at: string;
}

export interface WorkflowNode {
  id: number;
  key: string;
  node_type: string;
  label: string;
  config: Record<string, unknown>;
  position_x: number;
  position_y: number;
}

export interface WorkflowEdge {
  id: number;
  source_key: string;
  target_key: string;
  label: string;
}

export interface WorkflowRun {
  id: string;
  workflow_name: string;
  workflow_slug: string;
  status: string;
  trigger_source: string;
  context: Record<string, unknown>;
  error_message: string;
  started_at: string;
  finished_at: string | null;
  meaning?: MeaningContext;
}

export interface ApprovalRequest {
  id: number;
  run_id: string;
  workflow_name: string;
  title: string;
  description: string;
  status: string;
  approver_group: string;
  due_at: string | null;
  created_at: string;
  meaning?: MeaningContext;
}

export interface WorkflowTemplate {
  id: number;
  name: string;
  slug: string;
  category: string;
  description: string;
  definition: { nodes: unknown[]; edges: unknown[] };
}

export interface Connector {
  id: number;
  name: string;
  slug: string;
  kind: string;
  description: string;
}

export interface Notification {
  id: number;
  title: string;
  body: string;
  priority: string;
  is_read: boolean;
  link: string;
  created_at: string;
}

export interface DashboardStats {
  activeWorkflows: number;
  runsToday: number;
  pendingApprovals: number;
  failedRuns: number;
}
