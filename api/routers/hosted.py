"""Hosted cloud preview — paste GitHub URL, get a score without local install."""
from __future__ import annotations

import subprocess

from fastapi import APIRouter, HTTPException

from api.schemas import HostedPreviewIn, HostedPreviewOut
from api.services.github_hosted import preview_github_repository

router = APIRouter(prefix="/hosted", tags=["hosted"])


@router.post("/preview", response_model=HostedPreviewOut)
async def hosted_github_preview(body: HostedPreviewIn):
    """
    Clone a public GitHub repo (shallow), run AST scan, return Specwright Score.
    Designed for app.specwright.io — works on any machine with git installed.
    """
    try:
        result = preview_github_repository(body.github_url)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(502, str(e)) from e
    except subprocess.TimeoutExpired as e:
        raise HTTPException(504, "Repository clone timed out (120s limit).") from e
    except Exception as e:
        raise HTTPException(500, f"Preview scan failed: {e}") from e

    return HostedPreviewOut(**result)
