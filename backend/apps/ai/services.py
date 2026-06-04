from django.conf import settings

from apps.cases.models import Case
from apps.events.bus import publish_domain_event
from apps.events.types import EventType, Service

from .models import AIAssessment, AICopilotMessage
from .prompts import system_prompt, triage_user_prompt
from .providers import call_llm, heuristic_triage
from .verticals import PrimaryVertical, get_vertical, vertical_config


class AIService:
    @staticmethod
    def assert_case_allowed(org, case_type: str):
        cfg = vertical_config(org)
        if case_type not in cfg["case_types"]:
            raise ValueError(
                f"This organization runs {cfg['product_name']} only. "
                f"Case type '{case_type}' is not enabled."
            )

    @staticmethod
    def triage_case(*, case: Case, user) -> AIAssessment:
        org = case.organization
        vertical = get_vertical(org)
        payload = {
            "id": case.id,
            "title": case.title,
            "summary": case.summary,
            "case_type": case.case_type,
            "stage": case.stage,
            "priority": case.priority,
            "subject_key": case.subject_key,
            "subject_label": case.subject_label,
        }

        system = system_prompt(vertical)
        user_msg = triage_user_prompt(vertical, payload)
        result = call_llm(system=system, user=user_msg)
        model_name = getattr(settings, "AI_MODEL", "")
        provider = "llm"

        if not result:
            result = heuristic_triage(vertical, payload)
            model_name = "heuristic"
            provider = "heuristic"

        result["provider"] = provider

        assessment = AIAssessment.objects.create(
            organization=org,
            case=case,
            kind=AIAssessment.AssessmentKind.TRIAGE,
            vertical=vertical,
            prompt_snapshot={"system": system[:500], "user": user_msg[:1000]},
            result=result,
            confidence=float(result.get("confidence", 0.7)),
            model_name=model_name,
            requested_by=user,
        )

        publish_domain_event(
            service=Service.AI,
            event_type=EventType.AI_ASSESSMENT,
            organization_id=org.id,
            aggregate_type="ai_assessment",
            aggregate_id=assessment.id,
            actor_id=user.id,
            payload={"case_id": case.id, "kind": "triage"},
        )
        return assessment

    @staticmethod
    def copilot_turn(*, case: Case, user, message: str) -> AICopilotMessage:
        org = case.organization
        vertical = get_vertical(org)
        history = list(
            case.copilot_messages.order_by("created_at").values("role", "content")[-8:]
        )

        context = {
            "case": {
                "title": case.title,
                "stage": case.stage,
                "priority": case.priority,
                "summary": case.summary,
            },
            "history": history,
            "user_message": message,
        }

        system = system_prompt(vertical) + " Answer the operator's question in plain text (2-4 sentences) then JSON block with recommended_action."
        user_msg = f"Context:\n{context}\n\nOperator asks: {message}"

        llm_result = call_llm(system=system, user=user_msg)
        if llm_result and "answer" in llm_result:
            answer = llm_result.get("answer", llm_result.get("summary", ""))
        elif llm_result:
            answer = llm_result.get("summary", str(llm_result))
        else:
            answer = (
                f"Based on {vertical} playbook: prioritize «{case.title}». "
                f"Current stage is {case.get_stage_display()}. "
                f"Next: {heuristic_triage(vertical, context['case'])['recommended_action']}"
            )
            llm_result = heuristic_triage(vertical, context["case"])

        user_row = AICopilotMessage.objects.create(case=case, role="user", content=message)
        assessment = AIAssessment.objects.create(
            organization=org,
            case=case,
            kind=AIAssessment.AssessmentKind.COPILOT,
            vertical=vertical,
            prompt_snapshot={"message": message},
            result=llm_result if isinstance(llm_result, dict) else {"answer": answer},
            confidence=0.75,
            requested_by=user,
        )
        assistant_row = AICopilotMessage.objects.create(
            case=case,
            role="assistant",
            content=answer if isinstance(answer, str) else str(answer),
            assessment=assessment,
        )
        return assistant_row

    @staticmethod
    def nl_intake(*, org, user, natural_language: str) -> dict:
        """Natural-language case intake — AI extracts structured case from prose."""
        vertical = get_vertical(org)
        cfg = vertical_config(org)

        system = (
            system_prompt(vertical)
            + f" Extract a case from operator description. Allowed case_types: {cfg['case_types']}. "
            "Return JSON: title, case_type, summary, subject_label, priority (low|normal|high|critical)."
        )
        result = call_llm(system=system, user=natural_language)
        if not result:
            result = {
                "title": natural_language[:120],
                "case_type": cfg["case_types"][0],
                "summary": natural_language,
                "subject_label": "",
                "priority": "normal",
            }

        case_type = result.get("case_type", cfg["case_types"][0])
        AIService.assert_case_allowed(org, case_type)
        return result
