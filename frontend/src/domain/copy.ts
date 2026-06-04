/** Domain-specific language — never generic "records" or "items". */

export const CASE_STAGES = {
  intake: "Intake",
  investigation: "Investigation",
  resolution: "Resolution",
  post_review: "Post-Review",
} as const;

export const CASE_TYPES = {
  new_hire: "New hire request",
  policy_exception: "Policy exception",
  contract_review: "Contract review",
  shipment_exception: "Shipment exception",
  access_review: "Access review",
} as const;

export const VERTICAL_TERMS = {
  case: "Case",
  cases: "Cases",
  openCase: "Open a case",
  advanceStage: "Advance to next stage",
  runWorkflow: "Execute playbook",
  approval: "Sign-off",
  auditTrail: "Audit trail",
  complianceReport: "Compliance report",
  proactiveAlert: "Heads-up",
  memory: "Institutional memory",
  playbook: "Playbook",
  notWorkflow: "Playbook", // never "workflow" in user-facing HR/Legal copy
} as const;

export function stageGuidance(stage: string): string {
  const guides: Record<string, string> = {
    intake: "Capture the facts. Don't skip straight to resolution.",
    investigation: "Gather evidence, loop in the right approvers.",
    resolution: "Execute the fix — IT ticket, signature, carrier call.",
    post_review: "Close the loop. What do we change so this doesn't repeat?",
  };
  return guides[stage] ?? "";
}
