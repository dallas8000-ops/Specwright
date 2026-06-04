"""Aggregate multi-project view for engineering leads."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.tables import Project, Scan


def _parse_stats(scan: Scan | None) -> dict:
    if not scan or not scan.stats:
        return {}
    try:
        return json.loads(scan.stats)
    except json.JSONDecodeError:
        return {}


def _week_key(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _week_label(week_key: str) -> str:
    year, _, week = week_key.partition("-W")
    return f"W{week} '{year[2:]}"


async def build_team_dashboard(db: AsyncSession) -> dict:
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    result = await db.execute(select(Project).order_by(Project.name))
    projects = result.scalars().all()

    rows: list[dict] = []
    drifted: list[dict] = []
    weekly_scores: dict[str, list[int]] = defaultdict(list)
    project_trends: list[dict] = []

    total_score = 0
    scored_count = 0
    total_doc = 0
    total_test = 0
    metric_count = 0

    for project in projects:
        scan_result = await db.execute(
            select(Scan)
            .where(Scan.project_id == project.id, Scan.status == "completed")
            .order_by(Scan.created_at.desc())
            .limit(30)
        )
        scans = list(scan_result.scalars().all())
        latest = scans[0] if scans else None
        stats = _parse_stats(latest)

        score_obj = stats.get("score") or {}
        score = score_obj.get("score")
        if score is None and project.last_score:
            score = project.last_score

        breakdown = score_obj.get("breakdown") or {}
        drift = stats.get("drift") or {}
        metrics = stats.get("metrics") or {}

        doc_pct = breakdown.get("documentation_pct")
        test_pct = breakdown.get("test_coverage_pct")
        if doc_pct is not None:
            total_doc += doc_pct
            total_test += test_pct or 0
            metric_count += 1

        if score is not None:
            total_score += score
            scored_count += 1

        scanned_at = latest.created_at if latest else None
        if scanned_at and scanned_at.tzinfo is None:
            scanned_at = scanned_at.replace(tzinfo=timezone.utc)

        score_7d_ago = None
        for s in reversed(scans):
            if s.created_at and s.created_at.replace(tzinfo=timezone.utc) <= week_ago:
                old = _parse_stats(s).get("score", {}).get("score")
                if old is not None:
                    score_7d_ago = old
                break

        score_delta = None
        if score is not None and score_7d_ago is not None:
            score_delta = score - score_7d_ago

        drift_detected = bool(drift.get("drift_detected"))
        drift_this_week = drift_detected and scanned_at and scanned_at >= week_ago
        stale = not latest or (scanned_at and scanned_at < week_ago)
        never_scanned = latest is None

        needs_attention = never_scanned or drift_this_week or stale or (
            score is not None and score < 60
        )

        history = []
        for s in reversed(scans[-12:]):
            s_score = _parse_stats(s).get("score", {}).get("score")
            if s_score is None:
                continue
            at = s.created_at
            if at and at.tzinfo is None:
                at = at.replace(tzinfo=timezone.utc)
            history.append(
                {
                    "at": at.isoformat() if at else None,
                    "score": s_score,
                }
            )
            if at:
                weekly_scores[_week_key(at)].append(s_score)

        row = {
            "id": project.id,
            "name": project.name,
            "root_path": project.root_path,
            "framework": project.framework,
            "github_repo": project.github_repo or None,
            "watch_enabled": project.watch_enabled,
            "score": score,
            "grade": score_obj.get("grade"),
            "last_scanned_at": scanned_at.isoformat() if scanned_at else None,
            "documentation_pct": doc_pct,
            "test_coverage_pct": test_pct,
            "routes_found": stats.get("routes_found", 0),
            "drift_detected": drift_detected,
            "spec_in_sync": metrics.get("spec_in_sync", not drift_detected),
            "commits_behind": drift.get("commits_behind", 0),
            "score_delta_7d": score_delta,
            "needs_attention": needs_attention,
            "never_scanned": never_scanned,
            "drift_this_week": drift_this_week,
        }
        rows.append(row)

        if history:
            project_trends.append(
                {
                    "project_id": project.id,
                    "project_name": project.name,
                    "points": history,
                }
            )

        if drift_this_week or (stale and drift_detected) or never_scanned:
            drifted.append(
                {
                    **row,
                    "reason": (
                        "Never scanned"
                        if never_scanned
                        else "Spec drift detected this week"
                        if drift_this_week
                        else "Stale scan — spec may be behind code"
                        if stale
                        else "OpenAPI out of sync"
                    ),
                }
            )

    rows.sort(key=lambda r: (not r["needs_attention"], -(r["score"] or 0)))

    team_weeks = sorted(weekly_scores.keys())[-8:]
    team_trend = [
        {
            "week": wk,
            "label": _week_label(wk),
            "avg_score": round(sum(weekly_scores[wk]) / len(weekly_scores[wk])),
            "scan_count": len(weekly_scores[wk]),
        }
        for wk in team_weeks
    ]

    return {
        "summary": {
            "total_projects": len(projects),
            "scored_projects": scored_count,
            "avg_score": round(total_score / scored_count) if scored_count else None,
            "avg_documentation_pct": round(total_doc / metric_count, 1) if metric_count else None,
            "avg_test_coverage_pct": round(total_test / metric_count, 1) if metric_count else None,
            "drifted_this_week": len(drifted),
            "needs_attention": sum(1 for r in rows if r["needs_attention"]),
        },
        "projects": rows,
        "drifted_this_week": drifted,
        "team_trend": team_trend,
        "project_trends": project_trends,
    }
