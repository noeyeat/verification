#!/usr/bin/env python3
"""Playwright browser driver for control-taskboard.

Keeps a long-lived Chromium (CDP) under TASKBOARD_RUN_DIR so stepwise
`browser click|fill|…` commands preserve SPA view state. Teardown via
`control-taskboard cleanup` kills the browser process.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("TASKBOARD_BASE_URL", "http://127.0.0.1:8765")
STATE = Path(os.environ.get("TASKBOARD_RUN_DIR", Path(__file__).resolve().parents[1] / ".taskboard-run"))
STATE.mkdir(parents=True, exist_ok=True)
WS_FILE = STATE / "browser_ws.txt"
BROWSER_PID_FILE = STATE / "browser.pid"
CTX_DIR = STATE / "browser-profile"


def role_locator(page, role: str, name: str | None):
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    return page.get_by_role(role, **kwargs)


def _cdp_alive(endpoint: str) -> bool:
    try:
        urllib.request.urlopen(f"{endpoint.rstrip('/')}/json/version", timeout=1)
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def ensure_browser(p) -> str:
    """Return CDP HTTP endpoint; launch detached Chromium if needed."""
    endpoint = WS_FILE.read_text(encoding="utf-8").strip() if WS_FILE.exists() else ""
    if endpoint and _cdp_alive(endpoint):
        return endpoint

    for stale in (WS_FILE, BROWSER_PID_FILE):
        stale.unlink(missing_ok=True)

    port = int(os.environ.get("TASKBOARD_BROWSER_CDP_PORT", "0")) or _pick_free_port()
    endpoint = f"http://127.0.0.1:{port}"
    CTX_DIR.mkdir(parents=True, exist_ok=True)
    chrome = p.chromium.executable_path
    proc = subprocess.Popen(
        [
            chrome,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={str(CTX_DIR)}",
            "--headless=new",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    BROWSER_PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    WS_FILE.write_text(endpoint, encoding="utf-8")
    for _ in range(80):
        if _cdp_alive(endpoint):
            return endpoint
        if proc.poll() is not None:
            raise RuntimeError(f"browser exited early code={proc.returncode}")
        time.sleep(0.1)
    raise RuntimeError(f"browser CDP not ready at {endpoint}")


def get_page(p):
    """Connect to persistent CDP browser; preserve SPA state across CLI calls."""
    endpoint = ensure_browser(p)
    browser = p.chromium.connect_over_cdp(endpoint)
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    page = context.pages[0] if context.pages else context.new_page()
    url = page.url or ""
    if not url.startswith(BASE):
        page.goto(BASE, wait_until="networkidle")
    return browser, context, page


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="control-taskboard browser")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_goto = sub.add_parser("goto")
    p_goto.add_argument("--path", default="/")

    p_click = sub.add_parser("click")
    p_click.add_argument("--role", required=True)
    p_click.add_argument("--name", required=True)

    p_fill = sub.add_parser("fill")
    p_fill.add_argument("--role", required=True)
    p_fill.add_argument("--name", required=True)
    p_fill.add_argument("--value", required=True)

    p_press = sub.add_parser("press")
    p_press.add_argument("--key", required=True)

    p_snap = sub.add_parser("snapshot")
    p_snap.add_argument("--aria", action="store_true")
    p_snap.add_argument("--path", required=True)

    p_shot = sub.add_parser("screenshot")
    p_shot.add_argument("--path", required=True)

    p_eval = sub.add_parser("eval")
    p_eval.add_argument("--js", required=True)

    p_recipe = sub.add_parser("recipe")
    p_recipe.add_argument("name", choices=["create-task", "clear-completed", "filter-by-title"])
    p_recipe.add_argument("--evidence-dir", default=None)

    args = parser.parse_args(argv)

    with sync_playwright() as p:
        browser, context, page = get_page(p)
        try:
            if args.cmd == "goto":
                page.goto(BASE + args.path, wait_until="networkidle")
                print(json.dumps({"ok": True, "url": page.url}))
            elif args.cmd == "click":
                role_locator(page, args.role, args.name).click()
                page.wait_for_timeout(200)
                print(json.dumps({"ok": True, "clicked": args.name}))
            elif args.cmd == "fill":
                role_locator(page, args.role, args.name).fill(args.value)
                print(json.dumps({"ok": True, "filled": args.name}))
            elif args.cmd == "press":
                page.keyboard.press(args.key)
                print(json.dumps({"ok": True, "key": args.key}))
            elif args.cmd == "snapshot":
                out = Path(args.path)
                out.parent.mkdir(parents=True, exist_ok=True)
                snap = page.locator("body").aria_snapshot() if args.aria else page.content()
                out.write_text(snap if isinstance(snap, str) else str(snap), encoding="utf-8")
                print(json.dumps({"ok": True, "path": str(out)}))
            elif args.cmd == "screenshot":
                out = Path(args.path)
                out.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(out), full_page=True)
                print(json.dumps({"ok": True, "path": str(out)}))
            elif args.cmd == "eval":
                result = page.evaluate(args.js)
                print(json.dumps({"ok": True, "result": result}))
            elif args.cmd == "recipe":
                base_evid = Path(args.evidence_dir or os.environ.get("TASKBOARD_EVIDENCE_DIR", "artifacts"))
                # Reset SPA to home so recipes are independent of prior stepwise drives
                page.goto(BASE, wait_until="networkidle")
                if args.name == "create-task":
                    evid = base_evid / "create-task"
                    evid.mkdir(parents=True, exist_ok=True)
                    page.get_by_role("heading", name="All tasks").wait_for()
                    page.screenshot(path=str(evid / "01-home.png"), full_page=True)
                    page.get_by_role("button", name="New task").click()
                    page.get_by_role("form", name="Task editor").wait_for()
                    page.get_by_role("textbox", name="Title").fill("Release checklist")
                    page.get_by_role("textbox", name="Body").fill("Tag and publish")
                    page.screenshot(path=str(evid / "02-editor-filled.png"), full_page=True)
                    page.get_by_role("button", name="Save task").click()
                    page.get_by_role("heading", name="All tasks").wait_for()
                    page.get_by_role("link", name="Release checklist").wait_for()
                    page.get_by_role("link", name="Release checklist").click()
                    page.get_by_role("heading", name="Release checklist", level=3).wait_for()
                    aria = page.locator("body").aria_snapshot()
                    (evid / "03-detail.aria.txt").write_text(aria, encoding="utf-8")
                    page.screenshot(path=str(evid / "03-detail.png"), full_page=True)
                    page.get_by_role("button", name="Back to all tasks").click()
                    page.get_by_role("link", name="Release checklist").wait_for()
                    aria_list = page.locator("body").aria_snapshot()
                    (evid / "04-list.aria.txt").write_text(aria_list, encoding="utf-8")
                    page.screenshot(path=str(evid / "04-list.png"), full_page=True)
                    api = page.evaluate("async () => (await fetch('/api/tasks')).json()")
                    titles = [t["title"] for t in api.get("tasks", [])]
                    assert "Release checklist" in titles, titles
                    (evid / "05-api-list.json").write_text(json.dumps(api, indent=2), encoding="utf-8")
                    print(json.dumps({"ok": True, "feature": "create-task", "evidence": str(evid), "titles": titles}))
                elif args.name == "clear-completed":
                    evid = base_evid / "clear-completed"
                    evid.mkdir(parents=True, exist_ok=True)
                    page.get_by_role("heading", name="All tasks").wait_for()
                    page.get_by_role("button", name="New task").click()
                    page.get_by_role("textbox", name="Title").fill("Keep me open")
                    page.get_by_role("textbox", name="Body").fill("Should remain")
                    page.get_by_role("button", name="Save task").click()
                    page.get_by_role("link", name="Keep me open").wait_for()
                    page.get_by_role("button", name="New task").click()
                    page.get_by_role("textbox", name="Title").fill("Done chore")
                    page.get_by_role("textbox", name="Body").fill("Should be cleared")
                    page.get_by_role("button", name="Save task").click()
                    page.get_by_role("link", name="Done chore").wait_for()
                    page.screenshot(path=str(evid / "01-before-mark.png"), full_page=True)
                    (evid / "01-before-mark.aria.txt").write_text(
                        page.locator("body").aria_snapshot(), encoding="utf-8"
                    )
                    page.get_by_role("button", name="Mark complete: Done chore").click()
                    page.wait_for_timeout(300)
                    page.get_by_role("button", name="Mark incomplete: Done chore").wait_for()
                    page.screenshot(path=str(evid / "02-one-completed.png"), full_page=True)
                    (evid / "02-one-completed.aria.txt").write_text(
                        page.locator("body").aria_snapshot(), encoding="utf-8"
                    )
                    api_before = page.evaluate("async () => (await fetch('/api/tasks')).json()")
                    (evid / "02-api-before.json").write_text(
                        json.dumps(api_before, indent=2), encoding="utf-8"
                    )
                    done_titles = [t["title"] for t in api_before.get("tasks", []) if t.get("done")]
                    open_titles = [t["title"] for t in api_before.get("tasks", []) if not t.get("done")]
                    assert "Done chore" in done_titles, done_titles
                    assert "Keep me open" in open_titles, open_titles
                    page.get_by_role("button", name="Clear completed").click()
                    page.wait_for_timeout(300)
                    page.get_by_role("link", name="Keep me open").wait_for()
                    assert page.get_by_role("link", name="Done chore").count() == 0
                    page.screenshot(path=str(evid / "03-after-clear.png"), full_page=True)
                    aria_after = page.locator("body").aria_snapshot()
                    (evid / "03-after-clear.aria.txt").write_text(aria_after, encoding="utf-8")
                    api_after = page.evaluate("async () => (await fetch('/api/tasks')).json()")
                    (evid / "04-api-after.json").write_text(
                        json.dumps(api_after, indent=2), encoding="utf-8"
                    )
                    titles_after = [t["title"] for t in api_after.get("tasks", [])]
                    assert "Done chore" not in titles_after, titles_after
                    assert "Keep me open" in titles_after, titles_after
                    assert all(not t.get("done") for t in api_after.get("tasks", [])), api_after
                    print(
                        json.dumps(
                            {
                                "ok": True,
                                "feature": "clear-completed",
                                "evidence": str(evid),
                                "titles_after": titles_after,
                            }
                        )
                    )
                elif args.name == "filter-by-title":
                    evid = base_evid / "filter-by-title"
                    evid.mkdir(parents=True, exist_ok=True)
                    page.get_by_role("heading", name="All tasks").wait_for()
                    page.get_by_role("button", name="New task").click()
                    page.get_by_role("textbox", name="Title").fill("Alpha rocket")
                    page.get_by_role("textbox", name="Body").fill("launch notes")
                    page.get_by_role("button", name="Save task").click()
                    page.get_by_role("link", name="Alpha rocket").wait_for()
                    page.get_by_role("button", name="New task").click()
                    page.get_by_role("textbox", name="Title").fill("Beta notes")
                    page.get_by_role("textbox", name="Body").fill("alpha appears only in body")
                    page.get_by_role("button", name="Save task").click()
                    page.get_by_role("link", name="Beta notes").wait_for()
                    page.screenshot(path=str(evid / "01-all-tasks.png"), full_page=True)
                    (evid / "01-all-tasks.aria.txt").write_text(
                        page.locator("body").aria_snapshot(), encoding="utf-8"
                    )
                    page.get_by_role("searchbox", name="Filter by title").fill("alpha")
                    page.wait_for_timeout(200)
                    page.get_by_role("link", name="Alpha rocket").wait_for()
                    assert page.get_by_role("link", name="Beta notes").count() == 0
                    page.screenshot(path=str(evid / "02-filtered-alpha.png"), full_page=True)
                    (evid / "02-filtered-alpha.aria.txt").write_text(
                        page.locator("body").aria_snapshot(), encoding="utf-8"
                    )
                    page.get_by_role("searchbox", name="Filter by title").fill("zzz-nope")
                    page.wait_for_timeout(200)
                    assert "No matching tasks" in page.locator("#task-list").inner_text()
                    page.screenshot(path=str(evid / "03-no-match.png"), full_page=True)
                    (evid / "03-no-match.aria.txt").write_text(
                        page.locator("body").aria_snapshot(), encoding="utf-8"
                    )
                    page.get_by_role("button", name="Clear filter").click()
                    page.wait_for_timeout(200)
                    page.get_by_role("link", name="Alpha rocket").wait_for()
                    page.get_by_role("link", name="Beta notes").wait_for()
                    page.screenshot(path=str(evid / "04-cleared.png"), full_page=True)
                    (evid / "04-cleared.aria.txt").write_text(
                        page.locator("body").aria_snapshot(), encoding="utf-8"
                    )
                    page.get_by_role("button", name="Mark complete: Alpha rocket").click()
                    page.wait_for_timeout(300)
                    page.get_by_role("button", name="Mark incomplete: Alpha rocket").wait_for()
                    page.get_by_role("searchbox", name="Filter by title").fill("alpha")
                    page.wait_for_timeout(200)
                    page.get_by_role("link", name="Alpha rocket").wait_for()
                    assert page.get_by_role("link", name="Beta notes").count() == 0
                    page.screenshot(path=str(evid / "05-completed-filtered.png"), full_page=True)
                    (evid / "05-completed-filtered.aria.txt").write_text(
                        page.locator("body").aria_snapshot(), encoding="utf-8"
                    )
                    print(
                        json.dumps(
                            {
                                "ok": True,
                                "feature": "filter-by-title",
                                "evidence": str(evid),
                            }
                        )
                    )
        finally:
            # Leave the detached Chromium + open page alive for the next CLI call.
            # Do not call browser.close(): even over CDP it closes pages/contexts and
            # would wipe SPA state. Exiting sync_playwright disconnects the client only.
            pass
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
        raise
