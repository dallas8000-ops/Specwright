# Legacy Django backend — not supported

This directory is an earlier Django prototype of Specwright. It is **not deployed** and the
React UI in `frontend/` does not call it.

The supported, deployed backend is the FastAPI service in [`../api/`](../api/) — see the
root [README](../README.md) for setup.

The code is kept for reference; CI still runs its tests (`backend` job in
`.github/workflows/ci-smoke.yml`) so it stays importable. `docker-compose.yml` at the repo
root starts this legacy stack only.
