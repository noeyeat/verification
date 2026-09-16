# TaskBoard verification map

This directory is the maintained source for verifying the user-facing behavior of TaskBoard. Read the index before driving the app, then use the matching feature file as the recipe.

## Baseline preconditions

- Launch TaskBoard with `control-taskboard launch` so the instance uses a disposable data directory under `.taskboard-run/`.
- Default URL: `http://127.0.0.1:8765` (override with `TASKBOARD_PORT`).
- Seed with `control-taskboard seed` when a feature needs `Quarterly plan` and `Grocery list`.
- Put `scripts/` on `PATH` (or invoke `./scripts/control-taskboard`).
- Run `control-taskboard doctor` and require matching URL, data directory, and build id.
- Never drive an instance that was not started by this verification run.

## Driving conventions

- Start every recipe from the baseline state unless its preconditions say otherwise.
- Prefer ARIA roles and accessible names over CSS selectors or DOM position.
- Treat every command as literal. Keep quoted names and flags unchanged.
- Run browser actions through `control-taskboard browser`.
- Run API/CLI actions through `control-taskboard cli -- <command>`.
- Restore or re-seed disposable data after a mutation. Do not remove proof artifacts during cleanup.

## Proof and skip reporting

- Capture the user action and the resulting state, not only the final screen.
- UI proof includes an ARIA snapshot and a screenshot with the app identity visible.
- CLI proof includes the command, stdout, stderr, and exit code.
- Mutation proof includes a read-only second view of the stored value (detail page and/or `cli -- list`).
- Record the feature ID and entry point used with every artifact.
- Report an unreachable path with the attempted command and the unmet precondition.
- Do not report a skipped entry point as verified through a different path.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with control-taskboard` starts with `Preconditions:` and uses labeled bullets that pair each user action with an exact command and observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

Keep implementation details out of the map. Name only user paths, stable handles, required state, commands, and observable proof.

## Features

- [Home and list tasks](./home-list.md) covers the default landing list and empty state.
- [Create a task](./create-task.md) covers browser creation, cancellation, persistence, and CLI create.
- [Search tasks](./search.md) covers toolbar search with matching, empty, and clear states plus CLI search.
- [Open task detail](./task-detail.md) covers opening a task from the list and returning home.
- [Clear completed](./clear-completed.md) covers marking tasks done and removing all completed tasks while incomplete remain.
- [Filter by title](./filter-by-title.md) covers the home list title substring filter and clear.
