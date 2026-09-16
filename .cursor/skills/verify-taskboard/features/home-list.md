# Home and list tasks

Home shows every saved task title and body excerpt so a user can scan the board and open a task.

## Sub-features

- `home-open` shows the All tasks heading on load and via the Home button.
- `home-empty` shows an empty-state message when no tasks exist.
- `home-populated` lists seeded or created tasks with accessible links named by title.

## How to get to it (user POV)

- Open `http://127.0.0.1:8765/` (default after launch).
- Choose the `Home` button in the primary nav.

## Driving it with control-taskboard

Preconditions:

- TaskBoard is healthy at `http://127.0.0.1:8765`.
- `control-taskboard doctor` reports the expected URL and disposable data directory.

- **Landing list.** Open the app. Run `control-taskboard browser goto --path /`. A heading named `All tasks` is visible and the region shows TaskBoard chrome.
- **Empty state.** With an empty data dir, read the list. Run `control-taskboard browser snapshot --aria --path artifacts/home-list/empty.aria.txt`. The snapshot includes `No tasks yet`.
- **Populated list.** Seed demo tasks. Run `control-taskboard seed` then `control-taskboard browser click --role button --name "Home"`. Links named `Quarterly plan` and `Grocery list` appear under list `Task list`.
- **Proof.** Capture the populated home. Run `control-taskboard browser screenshot --path artifacts/home-list/home.png` and `control-taskboard browser snapshot --aria --path artifacts/home-list/home.aria.txt`. Both identify TaskBoard and the seeded titles.

## Gotchas

- After mutations, re-click `Home` (or wait for the list refresh) before asserting membership.
- Titles are the accessible names of the links — assert those names, not DOM order alone.
