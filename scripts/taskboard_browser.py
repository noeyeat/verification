#!/usr/bin/env python3
"""Playwright browser driver for control-taskboard."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("TASKBOARD_BASE_URL", "http://127.0.0.1:8765")
STATE = Path(os.environ.get("TASKBOARD_RUN_DIR", Path(__file__).resolve().parents[1] / ".taskboard-run"))
STATE.mkdir(parents=True, exist_ok=True)
WS_FILE = STATE / "browser_ws.txt"
CTX_DIR = STATE / "browser-profile"


def get_page(p):
    """Connect to an existing headed/headless browser or start one."""
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.goto(BASE, wait_until="networkidle")
    return browser, context, page


def role_locator(page, role: str, name: str | None):
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    return page.get_by_role(role, **kwargs)


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

    # one-shot recipe runner for create-task proof
    p_recipe = sub.add_parser("recipe")
    p_recipe.add_argument("name", choices=["create-task"])
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
                # accessibility snapshot via aria tree approximation
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
                evid = Path(args.evidence_dir or os.environ.get("TASKBOARD_EVIDENCE_DIR", "artifacts"))
                evid = evid / "create-task"
                evid.mkdir(parents=True, exist_ok=True)
                # Home visible
                page.get_by_role("heading", name="All tasks").wait_for()
                page.screenshot(path=str(evid / "01-home.png"), full_page=True)
                # Open create
                page.get_by_role("button", name="New task").click()
                page.get_by_role("form", name="Task editor").wait_for()
                page.get_by_role("textbox", name="Title").fill("Release checklist")
                page.get_by_role("textbox", name="Body").fill("Tag and publish")
                page.screenshot(path=str(evid / "02-editor-filled.png"), full_page=True)
                page.get_by_role("button", name="Save task").click()
                page.get_by_role("heading", name="All tasks").wait_for()
                page.get_by_role("link", name="Release checklist").wait_for()
                # Confirm persistence via second view
                page.get_by_role("link", name="Release checklist").click()
                page.get_by_role("heading", name="Release checklist", level=3).wait_for()
                aria = page.locator("body").aria_snapshot()
                (evid / "03-detail.aria.txt").write_text(aria, encoding="utf-8")
                page.screenshot(path=str(evid / "03-detail.png"), full_page=True)
                # Back to list and confirm still present
                page.get_by_role("button", name="Back to all tasks").click()
                page.get_by_role("link", name="Release checklist").wait_for()
                aria_list = page.locator("body").aria_snapshot()
                (evid / "04-list.aria.txt").write_text(aria_list, encoding="utf-8")
                page.screenshot(path=str(evid / "04-list.png"), full_page=True)
                # Side effect: API list contains the task
                api = page.evaluate("async () => (await fetch('/api/tasks')).json()")
                titles = [t["title"] for t in api.get("tasks", [])]
                assert "Release checklist" in titles, titles
                (evid / "05-api-list.json").write_text(json.dumps(api, indent=2), encoding="utf-8")
                print(json.dumps({"ok": True, "feature": "create-task", "evidence": str(evid), "titles": titles}))
        finally:
            context.close()
            browser.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
        raise
