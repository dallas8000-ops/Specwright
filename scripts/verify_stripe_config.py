#!/usr/bin/env python3
"""Verify live Stripe/Render billing config via public health endpoints."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API_URL = os.environ.get("SPECWRIGHT_API_URL", "https://specwright-api.onrender.com").rstrip("/")


def fetch(path: str) -> tuple[int, dict]:
    req = urllib.request.Request(f"{API_URL}{path}", headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except TimeoutError:
        return 0, {"error": "request timed out", "path": path}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode() if exc.fp else "{}"
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, {"raw": body}


def main() -> int:
    print(f"API: {API_URL}\n")

    status, body = fetch("/api/v1/health")
    print(f"GET /api/v1/health -> {status or 'timeout'}")
    print(json.dumps(body, indent=2))
    if status == 0:
        print("\nAPI unreachable. Check Render service or cold start.", file=sys.stderr)
        return 1

    status, body = fetch("/api/v1/health/billing")
    print(f"\nGET /api/v1/health/billing -> {status}")
    print(json.dumps(body, indent=2))

    billing = body.get("billing", {})
    missing = [k for k, ok in billing.items() if k.startswith("stripe_") and not ok]
    if status != 200 or missing:
        print("\nAction: set missing Render env vars:", ", ".join(missing), file=sys.stderr)
        print("See docs/STRIPE_RENDER_SETUP.md", file=sys.stderr)
        return 1

    print("\nStripe env vars are present on the API. Confirm webhook events in Stripe Dashboard.")
    print("Guide: docs/STRIPE_RENDER_SETUP.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
