import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.core.database import get_db
from api.models.tables import Artifact, Project, Scan
from api.schemas import ArtifactOut, ContextOut, ProjectCreate, ProjectOut, ScanOut
from api.services.project_slug import ensure_unique_slug
from api.services.scan_history import previous_openapi
from api.services.scan_runner import run_scan

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    root = body.root_path
    project = Project(
        name=body.name,
        root_path=root,
        framework=body.framework,
        github_repo=(body.github_repo or "").strip(),
    )
    db.add(project)
    await db.flush()
    project.public_slug = await ensure_unique_slug(db)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectOut])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.post("/{project_id}/scan", response_model=ScanOut)
async def scan_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    try:
        prev = await previous_openapi(db, project_id)
        scan = await run_scan(project, db, previous_openapi=prev)
        stats = json.loads(scan.stats or "{}")
        project.last_score = stats.get("score", {}).get("score", 0)
        await db.commit()
    except FileNotFoundError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"Scan failed: {e}") from e

    result = await db.execute(
        select(Scan).where(Scan.id == scan.id).options(selectinload(Scan.artifacts))
    )
    return result.scalar_one()


@router.get("/{project_id}/scans", response_model=list[ScanOut])
async def list_scans(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project_id)
        .options(selectinload(Scan.artifacts))
        .order_by(Scan.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{project_id}/context", response_model=ContextOut)
async def project_context(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    result = await db.execute(
        select(Scan)
        .where(Scan.project_id == project_id)
        .options(selectinload(Scan.artifacts))
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        return ContextOut(
            what_happened="Project connected but not scanned yet.",
            who="You pointed Specwright at this codebase.",
            why_it_matters="Undocumented APIs and missing tests cost hours every sprint.",
            what_next="Run a scan to generate OpenAPI, pytest scaffold, and model diagrams.",
        )
    return ContextOut(
        what_happened=scan.summary,
        who=f"Specwright analyzed `{project.root_path}`",
        why_it_matters="Shipping without docs/tests increases incident rate and slows onboarding.",
        what_next="Review generated artifacts, export to repo, wire into CI.",
    )


@router.get("/artifacts/{artifact_id}", response_model=ArtifactOut)
async def get_artifact(artifact_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Artifact).where(Artifact.id == artifact_id).options(selectinload(Artifact.scan))
    )
    art = result.scalar_one_or_none()
    if not art:
        raise HTTPException(404, "Artifact not found")
    return art
