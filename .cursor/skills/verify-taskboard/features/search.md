# Search tasks

Search lets a user find tasks by title or body text and distinguish no matches from a cleared query.

## Sub-features

- `search-open` opens search from the Search button.
- `search-match` returns title and body matches without changing task data.
- `search-empty` shows a complete empty state for a query with no matches.
- `search-clear` removes the query and clears results.
- `search-cli` returns the same matching tasks from the terminal helper.

## How to get to it (user POV)

- Choose the `Search` button in the primary nav.
- Run `control-taskboard cli -- search <query>` in a terminal.

## Driving it with control-taskboard

Preconditions:

- TaskBoard is healthy at `http://127.0.0.1:8765`.
- The disposable data directory contains `Quarterly plan` with body text `Draft budget` (run `control-taskboard seed`).
- `control-taskboard doctor` reports the expected URL and data directory.

- **Toolbar entry.** Choose `Search`. Run `control-taskboard browser click --role button --name "Search"`. Heading `Search tasks` appears with focus available in searchbox `Search tasks`.
- **Title match.** Type `quarterly`. Run `control-taskboard browser fill --role searchbox --name "Search tasks" --value "quarterly"`. The `Search results` list contains `Quarterly plan` and does not contain `Grocery list`.
- **Body match.** Replace the query with `budget`. Run `control-taskboard browser fill --role searchbox --name "Search tasks" --value "budget"`. The result `Quarterly plan` remains visible.
- **Empty state.** Enter `volcano`. Run `control-taskboard browser fill --role searchbox --name "Search tasks" --value "volcano"`. A status named `No matching tasks` appears.
- **Clear query.** Choose `Clear search`. Run `control-taskboard browser click --role button --name "Clear search"`. The searchbox is empty and results are cleared.
- **CLI match.** Search from the terminal. Run `control-taskboard cli -- search "quarterly"`. Exit code `0` and stdout contain `Quarterly plan`.
- **CLI miss.** Search for an absent value. Run `control-taskboard cli -- search "volcano"`. Exit code `0` and stdout show an empty `tasks` array.
- **Proof.** Capture the populated result state. Run `control-taskboard browser snapshot --aria --path artifacts/search/results.aria.txt` and `control-taskboard browser screenshot --path artifacts/search/results.png`. Both artifacts identify TaskBoard, the query context, and `Quarterly plan`.

## Gotchas

- Results update after a short debounce (~150ms). Wait for the results list or empty status, not a fixed race against typing.
- Opening a result (if navigated to detail) changes browser state. Reopen search before proving another query.
- The CLI returns JSON; assert on the `tasks` array titles.
