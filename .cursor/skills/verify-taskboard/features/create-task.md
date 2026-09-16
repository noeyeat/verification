# Create a task

Create task lets a user save a titled task from the browser or CLI, cancel an unfinished draft, and confirm the saved task from a second user-facing view.

## Sub-features

- `create-open` opens a blank editor from the New task button.
- `create-save` persists a title and body.
- `create-cancel` discards an unfinished browser draft.
- `create-cli` creates the same task shape from the terminal helper.

## How to get to it (user POV)

- Choose the `New task` button in the primary nav.
- Run `control-taskboard cli -- create --title <title> --body <body>` in a terminal.

## Driving it with control-taskboard

Preconditions:

- TaskBoard is healthy at `http://127.0.0.1:8765`.
- No task is titled `Release checklist`.
- `control-taskboard doctor` reports the expected URL and disposable data directory.

- **Open editor.** Choose `New task`. Run `control-taskboard browser click --role button --name "New task"`. A form named `Task editor` appears with focus available in the `Title` textbox.
- **Enter content.** Type the title and body. Run `control-taskboard browser fill --role textbox --name "Title" --value "Release checklist"` and `control-taskboard browser fill --role textbox --name "Body" --value "Tag and publish"`.
- **Save task.** Choose `Save task`. Run `control-taskboard browser click --role button --name "Save task"`. The `All tasks` heading returns and a link named `Release checklist` appears.
- **Confirm persistence.** Open the task and inspect detail. Run `control-taskboard browser click --role link --name "Release checklist"`. The detail heading level-3 reads `Release checklist` and the body shows `Tag and publish`.
- **Cancel draft.** Open a new task, enter `Discard me`, and choose `Cancel`. Run `control-taskboard browser click --role button --name "New task"`, `control-taskboard browser fill --role textbox --name "Title" --value "Discard me"`, and `control-taskboard browser click --role button --name "Cancel"`. The task list returns and has no `Discard me` link.
- **CLI entry.** Create a second task. Run `control-taskboard cli -- create --title "CLI note" --body "Created from terminal"`. Exit code `0` and stdout contain the new task title.
- **Proof.** Capture list and detail evidence. Prefer `control-taskboard browser recipe create-task`, or manually run `control-taskboard browser snapshot --aria --path artifacts/create-task/list.aria.txt` and `control-taskboard browser screenshot --path artifacts/create-task/list.png`. Artifacts must show `Release checklist`. Also keep `artifacts/create-task/05-api-list.json` (or `cli -- list` stdout) as the side-effect check.

## Gotchas

- Titles are trimmed on save. Assert the rendered title link, not the draft input value.
- A save status alone is insufficient proof. Reopen the task from the list (detail view) and/or confirm via `cli -- list`.
- Remove `Release checklist` and `CLI note` during fixture cleanup, but retain their proof artifacts.
- One-shot recipe: `control-taskboard browser recipe create-task` writes under `artifacts/create-task/`.
