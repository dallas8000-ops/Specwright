"""Shields-style SVG badges for README embeds (Codecov / Snyk pattern)."""
from __future__ import annotations

import html


def score_color(score: int | None) -> str:
    if score is None:
        return "#64748b"
    if score >= 85:
        return "#22c55e"
    if score >= 65:
        return "#eab308"
    return "#ef4444"


def render_score_badge(
    *,
    score: int | None,
    label: str = "Specwright Score",
) -> str:
    value = "—" if score is None else str(min(100, max(0, score)))
    color = score_color(score)

    label_w = max(92, len(label) * 7 + 14)
    value_w = max(28, len(value) * 8 + 12)
    total_w = label_w + value_w

    label_text = html.escape(label)
    value_text = html.escape(value)

    inner = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{total_w}" height="20" role="img" aria-label="{html.escape(label)}: {value_text}">
  <title>{label_text}: {value_text}</title>
  <g shape-rendering="crispEdges">
    <rect width="{label_w}" height="20" fill="#1e293b"/>
    <rect x="{label_w}" width="{value_w}" height="20" fill="{color}"/>
  </g>
  <g fill="#f8fafc" font-family="ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif" font-size="11" font-weight="600">
    <text x="{label_w / 2}" y="14" text-anchor="middle">{label_text}</text>
    <text x="{label_w + value_w / 2}" y="14" text-anchor="middle">{value_text}</text>
  </g>
</svg>"""
    return inner
