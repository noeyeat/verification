# Open task detail

Task detail shows the full title, body, and metadata for one task chosen from the list, and lets the user return to All tasks.

## Sub-features

- `detail-open` opens a task from its title link in the home list.
- `detail-content` shows title, body, and id/created metadata.
- `detail-back` returns to All tasks without losing the list.

## How to get to it (user POV)

- From Home, choose a task title link (accessible name equals the title).
- From detail, choose `Back to all tasks`.

## Driving it with control-taskboard

Preconditions:

- TaskBoard is healthy at `http://127.0.0.1:8765`.
- Seeded tasks include `Quarterly plan`.
- `control-taskboard doctor` reports the expected URL and data directory.

- **Open detail.** From Home, choose `Quarterly plan`. Run `control-taskboard browser click --role button --name "Home"` then `control-taskboard browser click --role link --name "Quarterly plan"`. Detail shows heading level-3 `Quarterly plan` and body `Draft budget`.
- **Back home.** Choose `Back to all tasks`. Run `control-taskboard browser click --role button --name "Back to all tasks"`. Heading `All tasks` returns and `Quarterly plan` remains listed.
- **Proof.** Run `control-taskboard browser screenshot --path artifacts/task-detail/detail.png` and `control-taskboard browser snapshot --aria --path artifacts/task-detail/detail.aria.txt` while detail is open. Artifacts show TaskBoard and `Quarterly plan`.

## Gotchas

- Detail is client-side only; refreshing the page returns to Home. Capture evidence before navigating away or reloading.
- Link names equal titles; duplicate titles would be ambiguous — avoid seeding duplicates in verification data.
