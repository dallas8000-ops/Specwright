"""Parse Django models and emit Mermaid ER diagrams + model reference docs."""
from __future__ import annotations

import ast
import re
from pathlib import Path


def collect_django_model_names(files: list[Path], root: Path) -> list[dict]:
    out = []
    for fp in files:
        if "model" not in fp.name.lower():
            continue
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        mod = str(fp.relative_to(root)).replace("\\", "/")
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                src = ast.unparse(node) if hasattr(ast, "unparse") else ""
                if "Model" in src or "models.Model" in src:
                    out.append({"name": node.name, "module": mod})
    return out


def analyze_django_models(files: list[Path], root: Path) -> tuple[str, str]:
    models = []
    for fp in files:
        if "models.py" not in fp.name and "models" not in str(fp):
            continue
        try:
            tree = ast.parse(fp.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        module = str(fp.relative_to(root)).replace("\\", "/")
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                src = ast.unparse(node) if hasattr(ast, "unparse") else node.name
                if "Model" not in src and "models.Model" not in src:
                    continue
                fields = _extract_fields(node)
                models.append({"name": node.name, "module": module, "fields": fields})

    mermaid = _mermaid_er(models)
    markdown = _markdown_models(models)
    return mermaid, markdown


def _extract_fields(class_node: ast.ClassDef) -> list[dict]:
    fields = []
    for item in class_node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    fields.append({"name": target.id, "type": _field_type(item.value)})
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            fields.append({"name": item.target.id, "type": _field_type(item.annotation or item.value)})
    return fields


def _field_type(node) -> str:
    if node is None:
        return "?"
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node, ast.Name):
        return node.id
    return ast.unparse(node) if hasattr(ast, "unparse") else "field"


def _mermaid_er(models: list[dict]) -> str:
    if not models:
        return "erDiagram\n  PLACEHOLDER {\n    string note\n  }"
    lines = ["erDiagram"]
    for m in models:
        lines.append(f"  {m['name']} {{")
        for f in m["fields"][:12]:
            col_type = re.sub(r"[^a-zA-Z0-9_]", "", f["type"])[:24] or "string"
            lines.append(f"    {col_type} {f['name']}")
        lines.append("  }")
    return "\n".join(lines)


def _markdown_models(models: list[dict]) -> str:
    if not models:
        return "# Django Models\n\nNo models detected."
    parts = ["# Django Model Reference\n", "_Auto-generated from codebase scan._\n"]
    for m in models:
        parts.append(f"\n## `{m['name']}`\n")
        parts.append(f"**Module:** `{m['module']}`\n")
        if m["fields"]:
            parts.append("| Field | Type |\n|-------|------|\n")
            for f in m["fields"]:
                parts.append(f"| `{f['name']}` | {f['type']} |\n")
    return "".join(parts)
