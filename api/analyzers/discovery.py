from pathlib import Path

FRAMEWORK_MARKERS = {
    "django": ["manage.py", "django"],
    "fastapi": ["fastapi", "uvicorn"],
}


def detect_framework(root: Path) -> str:
    if (root / "manage.py").exists():
        return "django"
    for path in root.rglob("requirements*.txt"):
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if "fastapi" in text:
            return "fastapi"
        if "django" in text:
            return "django"
    for path in root.rglob("pyproject.toml"):
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if "fastapi" in text:
            return "fastapi"
        if "django" in text:
            return "django"
    return "python"


def collect_python_files(root: Path, *, limit: int = 500) -> list[Path]:
    skip = {".venv", "venv", "node_modules", "__pycache__", ".git", "migrations", "dist", "build"}
    files: list[Path] = []
    for path in root.rglob("*.py"):
        if any(part in skip for part in path.parts):
            continue
        files.append(path)
        if len(files) >= limit:
            break
    return files
