"""Regression tests for the hosted GitHub preview.

Covers two fixes:
- the score is computed from the repository's real test files, not generated scaffolds;
- a missing git binary on the API host surfaces as an explicit, actionable 500.
"""
from pathlib import Path

from fastapi.testclient import TestClient

from api.routers import hosted as hosted_router
from api.services.github_hosted import _collect_existing_tests


def _write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_collects_real_test_files_by_convention(tmp_path):
    _write(tmp_path, "app/tests.py", "def test_a(): pass\n")
    _write(tmp_path, "pkg/test_models.py", "def test_b(): pass\n")
    _write(tmp_path, "pkg/models_test.py", "def test_c(): pass\n")
    _write(tmp_path, "pkg/api_tests.py", "def test_d(): pass\n")
    _write(tmp_path, "pkg/models.py", "NOT_A_TEST = 1\n")

    out = _collect_existing_tests(tmp_path)

    for rel in ("app/tests.py", "pkg/test_models.py", "pkg/models_test.py", "pkg/api_tests.py"):
        assert f"# file: {rel}" in out
    assert "NOT_A_TEST" not in out


def test_skips_vendored_and_tooling_directories(tmp_path):
    for skipped in (".git", ".venv", "venv", "node_modules", "__pycache__"):
        _write(tmp_path, f"{skipped}/test_vendored.py", f"VENDORED_{skipped.strip('._')} = 1\n")
    _write(tmp_path, "src/test_real.py", "def test_real(): pass\n")

    out = _collect_existing_tests(tmp_path)

    assert "VENDORED_" not in out
    assert "# file: src/test_real.py" in out


def test_repo_without_tests_scores_against_empty_input(tmp_path):
    _write(tmp_path, "main.py", "print('hi')\n")
    assert _collect_existing_tests(tmp_path).strip() == ""


def test_missing_git_returns_actionable_500(monkeypatch):
    from api.main import app

    def _no_git(url):
        raise FileNotFoundError("[WinError 2] The system cannot find the file specified: 'git'")

    monkeypatch.setattr(hosted_router, "preview_github_repository", _no_git)
    client = TestClient(app, raise_server_exceptions=False)

    resp = client.post("/api/v1/hosted/preview", json={"github_url": "https://github.com/octo/repo"})

    assert resp.status_code == 500
    assert "requires git" in resp.json()["detail"]
