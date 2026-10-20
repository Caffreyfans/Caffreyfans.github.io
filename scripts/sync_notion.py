"""Export only an explicitly approved root and its structural child pages.

No workspace search, database queries, link following, or synced-block expansion.
Unsupported blocks fail the build, rather than silently publishing incomplete docs.
"""
import html
import json
import os
from pathlib import Path
import re
import sys
import time
import uuid

import requests
import yaml

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / ".notion-build"
PAGES = {}
TOKEN = os.environ.get("NOTION_TOKEN", "")
ROOT = os.environ.get("NOTION_ROOT_PAGE_ID", "")


def uid(value):
    return str(uuid.UUID(value))


def api(path):
    for attempt in range(6):
        time.sleep(0.35)
        try:
            response = requests.get(
                "https://api.notion.com/v1/" + path,
                headers={"Authorization": "Bearer " + TOKEN,
                         "Notion-Version": "2026-03-11"},
                timeout=45,
                allow_redirects=False,
            )
        except requests.RequestException:
            if attempt == 5:
                raise RuntimeError("Notion network request failed") from None
            time.sleep(2 ** attempt)
            continue
        if response.status_code == 429 or response.status_code >= 500:
            time.sleep(min(120, float(response.headers.get("Retry-After", 2 ** attempt))))
            continue
        if response.status_code != 200:
            # Never log response bodies, request headers, tokens, or page contents.
            raise RuntimeError(f"Notion request failed: HTTP {response.status_code}")
        return response.json()
    raise RuntimeError("Notion retry limit reached")


def children(block_id, depth=0):
    if depth > 50:
        raise RuntimeError("Block depth limit exceeded")
    items, cursor = [], None
    while True:
        from urllib.parse import urlencode
        params = {"page_size": 100}
        if cursor:
            params["start_cursor"] = cursor
        data = api(f"blocks/{block_id}/children?" + urlencode(params))
        items.extend(data["results"])
        if not data.get("has_more"):
            break
        cursor = data["next_cursor"]
    for block in items:
        kind = block["type"]
        if kind in ("synced_block", "child_database", "link_to_page"):
            raise RuntimeError(f"Out-of-scope block type: {kind}")
        if block.get("has_children") and kind != "child_page":
            block["_children"] = children(block["id"], depth + 1)
    return items


def discover(page_id, depth=0):
    if page_id in PAGES or depth > 30 or len(PAGES) >= 500:
        raise RuntimeError("Duplicate page or page traversal limit exceeded")
    page = api("pages/" + page_id)
    if page.get("archived") or page.get("in_trash"):
        raise RuntimeError("Page unavailable for publication")
    title = next(
        ("".join(t.get("plain_text", "") for t in p["title"])
         for p in page["properties"].values() if p["type"] == "title"), "Untitled"
    )
    blocks = children(page_id)
    PAGES[page_id] = {"title": title, "blocks": blocks,
                      "file": "index.md" if page_id == ROOT else page_id + ".md"}
    nav = [{title: PAGES[page_id]["file"]}]

    def walk(items):
        for block in items:
            if block["type"] == "child_page":
                child_id = uid(block["id"])
                nav.append({block["child_page"]["title"]: discover(child_id, depth + 1)})
            else:
                walk(block.get("_children", []))
    walk(blocks)
    return nav


def escape(text):
    text = html.escape(text, quote=False)
    return re.sub(r"([\\`*_{}\[\]#|!])", r"\\\1", text)


def rich(items):
    # Render mentions as plain text; never retrieve their target or metadata.
    result = []
    for item in items:
        text = escape(item.get("plain_text", ""))
        annotations = item.get("annotations", {})
        if annotations.get("bold"):
            text = "**" + text + "**"
        if annotations.get("italic"):
            text = "*" + text + "*"
        # Links deliberately remain plain text in this conservative exporter.
        result.append(text)
    return "".join(result)


def render(blocks):
    chunks = []
    for block in blocks:
        kind = block["type"]
        value = block.get(kind, {})
        text = rich(value.get("rich_text", []))
        sub = block.get("_children", [])
        if kind == "child_page":
            page = PAGES[uid(block["id"])]
            content = f'[{escape(page["title"])}]({page["file"]})'
        elif kind == "paragraph":
            content = text
        elif kind.startswith("heading_"):
            content = "#" * (int(kind[-1]) + 1) + " " + text
        elif kind in ("bulleted_list_item", "numbered_list_item", "to_do"):
            prefix = "1. " if kind == "numbered_list_item" else "- "
            if kind == "to_do":
                prefix += "[x] " if value.get("checked") else "[ ] "
            content = prefix + text
            if sub:
                content += "\n\n" + "\n".join("    " + line for line in render(sub).splitlines())
            sub = []
        elif kind in ("quote", "callout"):
            content = "\n".join("> " + line for line in text.splitlines())
        elif kind == "code":
            raw = "".join(t.get("plain_text", "") for t in value["rich_text"])
            fence = "`" * max(3, 1 + max((len(s) for s in re.findall(r"`+", raw)), default=0))
            language = value.get("language", "")
            language = language if re.fullmatch(r"[\w+-]+", language) else ""
            content = f"{fence}{language}\n{raw}\n{fence}"
        elif kind == "divider":
            content = "---"
        elif kind in ("column_list", "column"):
            content = ""
        elif kind == "toggle":
            content = "**" + text + "**"
        elif kind == "table_of_contents":
            content = "[TOC]"
        else:
            raise RuntimeError(f"Unsupported block type: {kind}")
        chunks.append(content)
        if sub:
            chunks.append(render(sub))
    return "\n\n".join(chunks)


def main():
    global ROOT
    if not TOKEN or not ROOT:
        raise RuntimeError("Set NOTION_TOKEN and NOTION_ROOT_PAGE_ID")
    ROOT = uid(ROOT)
    if os.environ.get("NOTION_PUBLICATION_APPROVED") != ROOT:
        raise RuntimeError("Publication approval must equal the canonical root UUID")
    # Fail rather than delete or reuse an existing directory.
    if OUT.exists():
        raise RuntimeError(".notion-build already exists; use a fresh checkout")
    nav = discover(ROOT)
    rendered = {page["file"]: "# " + escape(page["title"]) + "\n\n" + render(page["blocks"])
                for page in PAGES.values()}
    (OUT / "docs").mkdir(parents=True)
    for filename, content in rendered.items():
        (OUT / "docs" / filename).write_text(content + "\n", encoding="utf-8")
    config = yaml.safe_load((BASE / "mkdocs.notion.yml").read_text(encoding="utf-8"))
    config["docs_dir"] = str(OUT / "docs")
    config["site_dir"] = str(OUT / "site")
    config["nav"] = nav
    (OUT / "mkdocs.yml").write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    print(f"Exported {len(PAGES)} approved pages")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError) as error:
        print(f"Sync stopped: {error}", file=sys.stderr)
        sys.exit(1)
