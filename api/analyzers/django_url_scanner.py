"""Discover Django URL routes from urls.py (path/include)."""
from __future__ import annotations

import ast
from pathlib import Path

from api.analyzers.fastapi_scanner import _markdown_api, _openapi_yaml


def _module_to_urls_path(root: Path, module: str) -> Path | None:
    """accounts.urls -> .../accounts/urls.py"""
    rel = module.replace(".", "/") + ".py"
    candidates = [
        root / rel,
        root / "apps" / "backend" / rel,
    ]
    for path in candidates:
        if path.is_file():
            return path
    for path in root.rglob("urls.py"):
        if path.as_posix().endswith(rel):
            return path
    return None


def _path_literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _guess_method(path: str, name: str) -> str:
    hint = f"{path}/{name}".lower()
    if any(k in hint for k in ("login", "register", "logout", "refresh", "create", "webhook", "run", "export", "pay")):
        return "POST"
    if "delete" in hint or "remove" in hint:
        return "DELETE"
    if "patch" in hint or "update" in hint:
        return "PATCH"
    if "put" in hint:
        return "PUT"
    return "GET"


def _parse_urlpatterns(tree: ast.AST) -> list[tuple[str, str | None, str | None]]:
    """Return list of (path_segment, include_module|None, route_name|None)."""
    entries: list[tuple[str, str | None, str | None]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.targets[0], ast.Name) or node.targets[0].id != "urlpatterns":
            continue
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            continue
        for elt in node.value.elts:
            if not isinstance(elt, ast.Call) or not isinstance(elt.func, ast.Name):
                continue
            if elt.func.id not in ("path", "re_path"):
                continue
            if not elt.args:
                continue
            segment = _path_literal(elt.args[0])
            if segment is None:
                continue
            include_mod = None
            name = None
            for kw in elt.keywords:
                if kw.arg == "name":
                    name = _path_literal(kw.value)
            if len(elt.args) > 1 and isinstance(elt.args[1], ast.Call):
                inner = elt.args[1]
                if isinstance(inner.func, ast.Name) and inner.func.id == "include":
                    if inner.args and isinstance(inner.args[0], ast.Constant):
                        if isinstance(inner.args[0].value, str):
                            include_mod = inner.args[0].value
            entries.append((segment, include_mod, name))
    return entries


def _join_url(prefix: str, segment: str) -> str:
    p = (prefix.rstrip("/") + "/" + segment.lstrip("/")).replace("//", "/")
    if not p.startswith("/"):
        p = "/" + p
    return p.replace("//", "/")


def collect_django_routes(files: list[Path], root: Path) -> list[dict]:
    """Flatten Django urlpatterns into route dicts compatible with Specwright."""
    urls_files = [fp for fp in files if fp.name == "urls.py"]
    if not urls_files:
        urls_files = list(root.rglob("urls.py"))[:40]

    routes: list[dict] = []
    seen: set[tuple[str, str]] = set()

    stack: list[tuple[Path, str]] = []
    for fp in urls_files:
        if "config/urls.py" in fp.as_posix().replace("\\", "/") or fp.name == "urls.py":
            stack.append((fp, ""))

    if not stack and urls_files:
        stack = [(urls_files[0], "")]

    visited: set[Path] = set()
    while stack:
        fp, prefix = stack.pop()
        if fp in visited:
            continue
        visited.add(fp)
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8"))
        except (SyntaxError, OSError):
            continue

        for segment, include_mod, name in _parse_urlpatterns(tree):
            if include_mod:
                child = _module_to_urls_path(root, include_mod)
                if child:
                    stack.append((child, _join_url(prefix, segment)))
                continue
            full_path = _join_url(prefix, segment)
            route_name = name or full_path.strip("/").replace("/", "_") or "route"
            method = _guess_method(full_path, route_name)
            key = (method, full_path)
            if key in seen:
                continue
            seen.add(key)
            module = str(fp.relative_to(root)).replace("\\", "/")
            routes.append(
                {
                    "method": method,
                    "path": full_path,
                    "name": route_name,
                    "module": module,
                    "summary": "Django URL route",
                }
            )

    return sorted(routes, key=lambda r: (r["path"], r["method"]))


def analyze_django_urls(files: list[Path], root: Path) -> tuple[str, str]:
    routes = collect_django_routes(files, root)
    if not routes:
        return "", ""
    return _openapi_yaml(routes), _markdown_api(routes)
