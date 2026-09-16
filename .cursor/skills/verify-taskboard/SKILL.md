---
name: verify-taskboard
description: "Drive the TaskBoard demo web UI (and its JSON CLI helpers) to prove user-facing behavior. Use when verifying TaskBoard features, after TaskBoard changes, or when asked to run /verify-taskboard."
---

# Verify TaskBoard

TaskBoard is a minimal demo task list served by `server.py`. Primary surface: browser UI at `http://127.0.0.1:$TASKBOARD_PORT`. Secondary surface: JSON HTTP API wrapped by `control-taskboard cli`.

Never drive a shared/user instance. Always launch an isolated run via this skill's helpers.

## Launch

```bash
export PATH="$PWD/scripts:$PATH"
export TASKBOARD_RUN_DIR="$PWD/.taskboard-run"
export TASKBOARD_EVIDENCE_DIR="$PWD/artifacts"
export TASKBOARD_PORT=8765
export TASKBOARD_DATA_DIR="$TASKBOARD_RUN_DIR/data"
export TASKBOARD_BUILD_ID=demo-1

control-taskboard launch --port "$TASKBOARD_PORT" --data-dir "$TASKBOARD_DATA_DIR" --build "$TASKBOARD_BUILD_ID"
control-taskboard seed
```

Ready when stdout includes `launched pid=...` and `curl -fsS http://127.0.0.1:$TASKBOARD_PORT/api/health` returns `"ok": true`.

Teardown: `control-taskboard cleanup` (alias: `stop`). Cleanup removes the process and `$TASKBOARD_RUN_DIR` scratch data; it does **not** delete `$TASKBOARD_EVIDENCE_DIR`.

First-time harness setup (once per checkout):

```bash
python3 -m venv .venv-harness
.venv-harness/bin/pip install -r requirements-harness.txt
.venv-harness/bin/playwright install chromium
```

`control-taskboard browser` also bootstraps the venv if missing.

## Doctor

```bash
control-taskboard doctor
```

Pass criteria: pid alive, `/api/health` answers, reported `app=TaskBoard`, `build`, `port`, and `data_dir` match this run's env. Fail closed if any mismatch — do not drive.

## Drive

Prefer ARIA roles and accessible names.

Browser (Playwright via harness):

```bash
control-taskboard browser click --role button --name "New task"
control-taskboard browser fill --role textbox --name "Title" --value "Release checklist"
control-taskboard browser fill --role textbox --name "Body" --value "Tag and publish"
control-taskboard browser click --role button --name "Save task"
control-taskboard browser snapshot --aria --path artifacts/create-task/list.aria.txt
control-taskboard browser screenshot --path artifacts/create-task/list.png
```

One-shot create-task proof recipe:

```bash
control-taskboard browser recipe create-task
control-taskboard browser recipe clear-completed
control-taskboard browser recipe filter-by-title
```

CLI / API helpers (same data store as the UI):

```bash
control-taskboard cli -- create --title "CLI note" --body "Created from terminal"
control-taskboard cli -- search "quarterly"
control-taskboard cli -- list
control-taskboard cli -- health
control-taskboard cli -- complete <task-id>
control-taskboard cli -- clear-completed
```

Stable handles from this app:

| UI control | Role / name |
|---|---|
| Home | button `Home` |
| New task | button `New task` |
| Search | button `Search` |
| Title field | textbox `Title` |
| Body field | textbox `Body` |
| Save | button `Save task` |
| Cancel | button `Cancel` |
| Search box | searchbox `Search tasks` |
| Clear search | button `Clear search` |
| Task list | list `Task list` |
| Search results | list `Search results` |
| Back | button `Back to all tasks` |
| Clear completed | button `Clear completed` |
| Filter by title | searchbox `Filter by title` |
| Clear filter | button `Clear filter` |
| Mark complete | button `Mark complete: <title>` |
| Mark incomplete | button `Mark incomplete: <title>` |

Feature recipes live in `features/`. Drive mapped entry points from those files; do not invent alternate selectors.

## Evidence

Store proof under `artifacts/<feature-id>/` (or `$TASKBOARD_EVIDENCE_DIR/<feature-id>/`).

Standards:

- Exercise the real UI path (or documented CLI) — not admin-only internals. `/api/seed` is verification scaffolding for disposable data dirs only; do not count seeding as feature proof.
- Capture the action **and** the resulting state (e.g. editor filled + list after save + detail reopen).
- Verify side effects: `tasks.json` under the disposable data dir and/or `GET /api/tasks` must show the saved title.
- UI proof: ARIA snapshot + screenshot with "TaskBoard" visible.
- CLI proof: command, stdout, stderr, exit code.
- Evidence must survive `control-taskboard cleanup`.

## Cleanup

```bash
control-taskboard cleanup
```

Kills only the pid recorded at launch. Removes `.taskboard-run/` scratch (pid, log, meta, data). Keeps `artifacts/`.

## Helpers

| Helper | Invocation |
|---|---|
| Control CLI | `scripts/control-taskboard <launch\|doctor\|cleanup\|seed\|cli\|browser>` |
| Browser driver | invoked via `control-taskboard browser ...` → `scripts/taskboard_browser.py` |
| App server | `python3 server.py` (prefer `control-taskboard launch`) |

Put `scripts/` on `PATH` or invoke as `./scripts/control-taskboard`.
