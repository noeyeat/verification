# Filter by title

Home title filter narrows the visible task list by a case-insensitive title substring without calling Search or changing task data.

## Sub-features

- `filter-match` shows only tasks whose titles contain the query.
- `filter-empty` shows an empty list message when nothing matches.
- `filter-clear` restores the full home list.
- `filter-completed` applies the same title filter to completed tasks.

## How to get to it (user POV)

- On Home, type in the `Filter by title` searchbox above the task list.
- Choose `Clear filter` to remove the query and show all tasks again.

## Driving it with control-taskboard

Preconditions:

- TaskBoard is healthy at `http://127.0.0.1:8765`.
- Disposable data dir has tasks with distinct titles such as `Alpha rocket` and `Beta notes` (create via UI or CLI; seed alone is not required).
- `control-taskboard doctor` reports the expected URL and disposable data directory.

- **Create distinct titles.** Save `Alpha rocket` and `Beta notes` via New task or `control-taskboard cli -- create --title "Alpha rocket" --body "one"` and `cli -- create --title "Beta notes" --body "two"`. Both links appear on Home.
- **Filter match.** Type `alpha` in Filter by title. Run `control-taskboard browser fill --role searchbox --name "Filter by title" --value "alpha"`. The Task list shows `Alpha rocket` and does not show `Beta notes`.
- **Empty state.** Replace the query with `zzz-nope`. Run `control-taskboard browser fill --role searchbox --name "Filter by title" --value "zzz-nope"`. The list shows `No matching tasks`.
- **Clear filter.** Choose `Clear filter`. Run `control-taskboard browser click --role button --name "Clear filter"`. Both `Alpha rocket` and `Beta notes` are visible again.
- **Completed still filters.** Mark `Alpha rocket` complete, then filter `alpha` again. Run `control-taskboard browser click --role button --name "Mark complete: Alpha rocket"`, then fill Filter by title with `alpha`. `Alpha rocket` remains visible while `Beta notes` does not.
- **Proof.** Prefer `control-taskboard browser recipe filter-by-title`, which writes under `artifacts/filter-by-title/` (filtered, cleared, and completed-filter screenshots plus ARIA). Artifacts must show title-only filtering on Home, not the Search page.

## Gotchas

- This is the Home list filter (title only, client-side). Do not confuse it with the Search nav page (`Search tasks` / `/api/tasks?q=`), which matches title or body.
- Clearing the filter must restore incomplete and completed tasks that were already on the home list; it does not re-fetch differently from an unfiltered refresh.
- After `refreshHome` (e.g. Clear completed or toggle done), the current filter query still applies if the searchbox is non-empty.
- One-shot recipe: `control-taskboard browser recipe filter-by-title`.
