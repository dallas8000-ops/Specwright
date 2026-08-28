"""Grounded AI features (Pro+): descriptions, migration notes, tests, chat."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.models.tables import Project
from api.schemas import (
    AiBreakingChangeOut,
    AiChatIn,
    AiChatOut,
    AiDescriptionsOut,
    AiMigrationNoteOut,
    AiReconcileOut,
    AiSuiteOut,
    AiTestsOut,
)
from api.services.ai_breaking_change import classify_pr_diff
from api.services.ai_chat import ask_api_question
from api.services.ai_client import ai_configured
from api.services.ai_context import load_project_scan_context
from api.services.ai_descriptions import fill_openapi_descriptions, find_description_gaps
from api.services.ai_docstring_reconcile import reconcile_docstrings
from api.services.ai_migration_note import generate_migration_note
from api.services.ai_test_bodies import enhance_test_scaffold
from api.services.scan_history import previous_openapi_score
from pathlib import Path
from api.analyzers.discovery import collect_python_files

router = APIRouter(prefix="/projects", tags=["ai"])


def _require_ai_pro(project: Project) -> None:
    if not ai_configured():
        raise HTTPException(400, "Set SPECWRIGHT_AI_API_KEY to enable AI features.")
    if project.plan not in ("pro", "enterprise"):
        raise HTTPException(402, "AI features require Pro or Enterprise.")


@router.get("/{project_id}/ai/suite", response_model=AiSuiteOut)
async def ai_suite(project_id: int, db: AsyncSession = Depends(get_db)):
    """Non-LLM insights + counts; LLM actions available when configured."""
    try:
        project, scan, stats, routes, by_kind = await load_project_scan_context(db, project_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e

    pr_diff = stats.get("pr_diff")
    triage = classify_pr_diff(pr_diff)
    openapi = by_kind.get("openapi", "")
    mismatches = reconcile_docstrings(routes, openapi)
    gaps = find_description_gaps(routes, openapi)

    return AiSuiteOut(
        ai_available=ai_configured(),
        plan=project.plan,
        description_gaps=len(gaps),
        docstring_mismatches=len(mismatches),
        breaking_change=triage,
        pr_diff=pr_diff,
        score=stats.get("score", {}).get("score"),
    )


@router.post("/{project_id}/ai/descriptions", response_model=AiDescriptionsOut)
async def ai_fill_descriptions(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    _require_ai_pro(project)
    try:
        _, scan, _, routes, by_kind = await load_project_scan_context(db, project_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e

    openapi = by_kind.get("openapi", "")
    result = await fill_openapi_descriptions(routes, openapi)

    art = next((a for a in scan.artifacts if a.kind == "openapi"), None)
    if art and result["filled"] > 0:
        art.content = result["openapi"]
        await db.commit()

    return AiDescriptionsOut(
        filled=result["filled"],
        gaps_found=len(result.get("gaps", [])),
        openapi=result["openapi"],
        updates=result.get("updates", []),
    )


@router.post("/{project_id}/ai/migration-note", response_model=AiMigrationNoteOut)
async def ai_migration_note(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    _require_ai_pro(project)
    try:
        _, _, stats, _, _ = await load_project_scan_context(db, project_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e

    prev_score = await previous_openapi_score(db, project_id)
    result = await generate_migration_note(
        pr_diff=stats.get("pr_diff"),
        score=stats.get("score", {}).get("score"),
        previous_score=prev_score,
        project_name=project.name,
    )
    return AiMigrationNoteOut(note=result["note"], triage=result["triage"])


@router.get("/{project_id}/ai/breaking-changes", response_model=AiBreakingChangeOut)
async def ai_breaking_changes(project_id: int, db: AsyncSession = Depends(get_db)):
    try:
        _, _, stats, _, _ = await load_project_scan_context(db, project_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    triage = classify_pr_diff(stats.get("pr_diff"))
    return AiBreakingChangeOut(**triage)


@router.get("/{project_id}/ai/reconcile", response_model=AiReconcileOut)
async def ai_reconcile(project_id: int, db: AsyncSession = Depends(get_db)):
    try:
        _, _, _, routes, by_kind = await load_project_scan_context(db, project_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e
    items = reconcile_docstrings(routes, by_kind.get("openapi", ""))
    return AiReconcileOut(mismatches=items, count=len(items))


@router.post("/{project_id}/ai/tests", response_model=AiTestsOut)
async def ai_enhance_tests(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    _require_ai_pro(project)
    try:
        _, scan, stats, routes, _ = await load_project_scan_context(db, project_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e

    from api.analyzers.django_models import collect_django_model_names

    root = Path(project.root_path).resolve()
    files = collect_python_files(root)
    models = collect_django_model_names(files, root)
    framework = stats.get("framework", project.framework)

    result = await enhance_test_scaffold(
        framework=framework,
        routes=routes,
        models=models,
        project_name=project.name,
        root=root,
    )

    art = next((a for a in scan.artifacts if a.kind == "tests"), None)
    if art and result["enhanced"] > 0:
        art.content = result["content"]
        await db.commit()

    return AiTestsOut(content=result["content"], enhanced=result["enhanced"])


@router.post("/{project_id}/ai/chat", response_model=AiChatOut)
async def ai_chat(
    project_id: int, body: AiChatIn, db: AsyncSession = Depends(get_db)
):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    _require_ai_pro(project)
    try:
        _, _, _, routes, by_kind = await load_project_scan_context(db, project_id)
    except LookupError as e:
        raise HTTPException(404, str(e)) from e

    root = Path(project.root_path).resolve()
    result = await ask_api_question(
        question=body.question,
        routes=routes,
        openapi=by_kind.get("openapi", ""),
        api_md=by_kind.get("api_docs", ""),
        root=root,
    )
    return AiChatOut(**result)
