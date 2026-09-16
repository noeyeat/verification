# TaskBoard (verification demo)

Minimal demo web app used to exercise a project-local verification skill. Not a product.

## Run

```bash
TASKBOARD_PORT=8765 TASKBOARD_DATA_DIR=./data python3 server.py
```

Then open `http://127.0.0.1:8765`.

Isolation: set `TASKBOARD_PORT` and `TASKBOARD_DATA_DIR` (and optionally `TASKBOARD_HOST`, `TASKBOARD_BUILD_ID`) so concurrent instances do not collide.

## Features

- **Home** — list all tasks
- **New task** — create a titled task with optional body
- **Search** — filter tasks by title or body text

## Verification

See `.cursor/skills/verify-taskboard/` and `scripts/control-taskboard`.

Harness (once):

```bash
python3 -m venv .venv-harness
.venv-harness/bin/pip install -r requirements-harness.txt
.venv-harness/bin/playwright install chromium
```
