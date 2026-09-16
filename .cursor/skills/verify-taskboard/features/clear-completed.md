# Clear completed

Clear completed removes every task marked done and leaves incomplete tasks on the home list.

## Sub-features

- `mark-complete` marks a listed task done via its per-task control.
- `clear-completed` removes all done tasks in one action.
- `incomplete-remain` keeps incomplete tasks after clear.
- `clear-cli` clears completed tasks through the terminal helper.

## How to get to it (user POV)

- On Home, choose `Done` on a task (accessible name `Mark complete: <title>`), then choose `Clear completed`.
- Run `control-taskboard cli -- clear-completed` after marking tasks done via `cli -- complete <id>`.

## Driving it with control-taskboard

Preconditions:

- TaskBoard is healthy at `http://127.0.0.1:8765`.
- Disposable data dir has no tasks titled `Done chore` or `Keep me open` (or re-seed / empty first).
- `control-taskboard doctor` reports the expected URL and disposable data directory.

- **Create incomplete task.** Choose `New task`, save title `Keep me open`. Run `control-taskboard browser click --role button --name "New task"`, fill Title/Body, then `control-taskboard browser click --role button --name "Save task"`. A link named `Keep me open` appears.
- **Create and complete a task.** Save title `Done chore`, then choose `Mark complete: Done chore`. Run create steps as above, then `control-taskboard browser click --role button --name "Mark complete: Done chore"`. The control becomes `Mark incomplete: Done chore`.
- **Clear completed.** Choose `Clear completed`. Run `control-taskboard browser click --role button --name "Clear completed"`. The list still has `Keep me open` and no longer has `Done chore`.
- **Confirm side effect.** Run `control-taskboard cli -- list`. Stdout tasks include `Keep me open` with `done` false/absent of completed peers; `Done chore` is absent.
- **CLI entry.** After `cli -- create` and `cli -- complete <id>`, run `control-taskboard cli -- clear-completed`. Exit code `0`; `removed` ≥ 1 when completed tasks existed.
- **Proof.** Prefer `control-taskboard browser recipe clear-completed`, which writes under `artifacts/clear-completed/` (before/after screenshots, ARIA snapshots, API JSON). Artifacts must show completed gone and incomplete remaining.

## Gotchas

- Accessible names for mark controls include the task title (`Mark complete: Done chore`). Prefer those over the visible `Done`/`Undo` label alone when driving.
- Clearing with zero completed tasks is a no-op (`removed: 0`); that is not sufficient proof of the feature.
- Seed alone is not proof. Drive mark + clear through the UI (or documented CLI) and capture after-state evidence.
- One-shot recipe: `control-taskboard browser recipe clear-completed`.
