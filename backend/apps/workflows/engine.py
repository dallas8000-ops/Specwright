"""
Workflow execution engine — traverses DAG nodes, evaluates conditions,
invokes integrations, and manages approval gates.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class StepResult:
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    wait_for_human: bool = False
    wait_for_approval: bool = False


class WorkflowEngine:
    def __init__(self, run):
        self.run = run
        self.workflow = run.workflow
        self.context: dict[str, Any] = dict(run.context or {})
        self._handlers = {
            "trigger": self._handle_trigger,
            "action": self._handle_action,
            "condition": self._handle_condition,
            "approval": self._handle_approval,
            "delay": self._handle_delay,
            "transform": self._handle_transform,
            "notification": self._handle_notification,
            "integration": self._handle_integration,
            "human_task": self._handle_human_task,
            "parallel": self._handle_parallel,
            "join": self._handle_join,
            "subflow": self._handle_subflow,
        }

    def execute_node(self, node) -> StepResult:
        from apps.executions.models import StepRun

        step_run, _ = StepRun.objects.get_or_create(
            run=self.run,
            node_key=node.key,
            defaults={"node_type": node.node_type, "status": StepRun.Status.RUNNING},
        )
        step_run.status = StepRun.Status.RUNNING
        step_run.started_at = timezone.now()
        step_run.save(update_fields=["status", "started_at"])

        handler = self._handlers.get(node.node_type, self._handle_action)
        try:
            result = handler(node)
        except Exception as exc:
            logger.exception("Node %s failed", node.key)
            result = StepResult(success=False, error=str(exc))

        step_run.output = result.output
        step_run.status = (
            StepRun.Status.WAITING
            if result.wait_for_human or result.wait_for_approval
            else StepRun.Status.COMPLETED
            if result.success
            else StepRun.Status.FAILED
        )
        step_run.error_message = result.error or ""
        step_run.finished_at = timezone.now()
        step_run.save()

        from apps.executions.services import ExecutionService

        ExecutionService.step_completed(
            self.run,
            node_key=node.key,
            node_type=node.node_type,
            status=step_run.status,
        )
        if step_run.status == step_run.Status.WAITING:
            ExecutionService.run_status_changed(self.run, node_key=node.key)

        if result.success and result.output:
            self.context.setdefault("steps", {})[node.key] = result.output
            self.run.context = self.context
            self.run.save(update_fields=["context"])

        return result

    def get_next_nodes(self, current_node, result: StepResult):
        edges = self.workflow.edges.filter(source=current_node)
        if current_node.node_type == "condition":
            branch = result.output.get("branch", "default")
            matched = [e.target for e in edges if e.label == branch]
            if matched:
                return matched
            return [e.target for e in edges if not e.label]
        if not result.success:
            error_edges = edges.filter(label="on_error")
            if error_edges.exists():
                return [e.target for e in error_edges]
            return []
        return [e.target for e in edges]

    def run_from(self, start_key: str | None = None):
        from apps.executions.models import WorkflowRun

        nodes = {n.key: n for n in self.workflow.nodes.all()}
        if not nodes:
            self.run.status = WorkflowRun.Status.FAILED
            self.run.error_message = "Workflow has no nodes"
            self.run.save()
            return

        if start_key:
            queue = [nodes[start_key]]
        else:
            triggers = [n for n in nodes.values() if n.node_type == "trigger"]
            queue = triggers[:1] or list(nodes.values())[:1]

        visited: set[str] = set()
        while queue:
            node = queue.pop(0)
            if node.key in visited:
                continue
            visited.add(node.key)

            result = self.execute_node(node)
            if result.wait_for_approval or result.wait_for_human:
                self.run.status = WorkflowRun.Status.WAITING
                self.run.save(update_fields=["status"])
                return

            if not result.success:
                self.run.status = WorkflowRun.Status.FAILED
                self.run.error_message = result.error or "Step failed"
                self.run.finished_at = timezone.now()
                self.run.save()
                return

            for next_node in self.get_next_nodes(node, result):
                if next_node.key not in visited:
                    queue.append(next_node)

        self.run.status = WorkflowRun.Status.COMPLETED
        self.run.finished_at = timezone.now()
        self.run.save()

    def _handle_trigger(self, node) -> StepResult:
        return StepResult(success=True, output={"triggered": True, **node.config})

    def _handle_action(self, node) -> StepResult:
        action = node.config.get("action", "noop")
        return StepResult(success=True, output={"action": action, "completed": True})

    def _handle_condition(self, node) -> StepResult:
        expression = node.config.get("expression", "default")
        branch = self._evaluate_expression(expression, node.config)
        return StepResult(success=True, output={"branch": branch, "expression": expression})

    def _handle_approval(self, node) -> StepResult:
        from apps.approvals.models import ApprovalRequest
        from apps.approvals.services import create_approval_request

        if ApprovalRequest.objects.filter(
            run=self.run, node_key=node.key, status=ApprovalRequest.Status.PENDING
        ).exists():
            return StepResult(success=True, wait_for_approval=True)

        create_approval_request(self.run, node, self.context)
        return StepResult(success=True, wait_for_approval=True)

    def _handle_delay(self, node) -> StepResult:
        seconds = node.config.get("seconds", 0)
        resume_at = timezone.now() + timedelta(seconds=seconds)
        return StepResult(
            success=True,
            output={"delayed_seconds": seconds, "resume_at": resume_at.isoformat()},
        )

    def _handle_transform(self, node) -> StepResult:
        mapping = node.config.get("mapping", {})
        output = {target: self._resolve_path(source) for target, source in mapping.items()}
        return StepResult(success=True, output=output)

    def _handle_notification(self, node) -> StepResult:
        from apps.notifications.services import send_workflow_notification

        send_workflow_notification(self.run, node, self.context)
        return StepResult(success=True, output={"notified": True})

    def _handle_integration(self, node) -> StepResult:
        from apps.integrations.executor import execute_integration_step

        return execute_integration_step(node, self.context, self.run)

    def _handle_human_task(self, node) -> StepResult:
        return StepResult(success=True, wait_for_human=True, output={"task": node.config})

    def _handle_parallel(self, node) -> StepResult:
        return StepResult(success=True, output={"parallel": node.key})

    def _handle_join(self, node) -> StepResult:
        return StepResult(success=True, output={"joined": node.key})

    def _handle_subflow(self, node) -> StepResult:
        subflow_slug = node.config.get("workflow_slug")
        return StepResult(success=True, output={"subflow": subflow_slug, "delegated": True})

    def _evaluate_expression(self, expression: str, config: dict) -> str:
        ctx = self.context.get("input", {})
        if expression == "legal_review_required":
            if ctx.get("department") == "legal":
                return config.get("true_branch", "yes")
            amount = float(ctx.get("amount", 0) or 0)
            if amount > 50000:
                return config.get("true_branch", "yes")
            return config.get("false_branch", "no")

        match = re.match(r"(\w+)\s*>\s*(\d+)", expression)
        if match:
            field_name, threshold = match.groups()
            value = float(ctx.get(field_name, 0) or 0)
            return config.get("true_branch", "yes") if value > float(threshold) else config.get(
                "false_branch", "no"
            )

        return config.get("default_branch", "default")

    def _resolve_path(self, path: str) -> Any:
        data: Any = self.context
        for part in path.split("."):
            if isinstance(data, dict):
                data = data.get(part)
            else:
                return None
        return data
